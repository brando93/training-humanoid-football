"""Entrenamiento SEGURO: envuelve protomotions/train_agent.py y agrega, sin modificar ProtoMotions:

0. Normalización congelada: las estadísticas con que el modelo normaliza lo que ve (aprendidas con los datos
   de NVIDIA) no se actualizan con nuestros pocos clips; si se desplazan, el modelo "ve distinto" aunque sus
   pesos no cambien. Es lo mismo que hace el ajuste fino PEFT de NVIDIA (FREEZE_NORM=1 por defecto).
1. Calentamiento del crítico: el actor queda congelado (tasa 0) las primeras WARMUP_EPOCHS épocas, para que el
   crítico aprenda a juzgar antes de tocar la política.
2. Freno por empeoramiento: si la evaluación interna cae más de MARGIN por debajo del punto de partida en
   PATIENCE evaluaciones seguidas, se detiene (y last.ckpt queda, pero el candidato es el MEJOR: score_based).
3. Límite de tiempo contado desde la primera época (no desde el arranque de Isaac Sim): TRAIN_MIN.
4. Estado en <save_dir>/safe_train.json: puntaje inicial, cada evaluación, mejor puntaje y motivo de parada.

Uso (desde third_party/ProtoMotions o $PROTOMOTIONS_ROOT), mismos argumentos que train_agent.py:
  TRAIN_MIN=35 WARMUP_EPOCHS=20 python <repo>/training/train_safe.py --robot-name anatomic_soma ...
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

TRAIN_MIN = float(os.environ.get("TRAIN_MIN", "35"))
WARMUP_EPOCHS = int(os.environ.get("WARMUP_EPOCHS", "20"))
FREEZE_NORM = os.environ.get("FREEZE_NORM", "1") == "1"
MARGIN = float(os.environ.get("ABORT_MARGIN", "0.05"))
PATIENCE = int(os.environ.get("ABORT_PATIENCE", "2"))


class SafeTrain:
    def __init__(self, save_dir: Path):
        self.save_dir = save_dir
        self.t0 = None
        self.frozen_lrs = None
        self.state = {"train_min": TRAIN_MIN, "warmup_epochs": WARMUP_EPOCHS, "margin": MARGIN,
                      "start_score": None, "best_score": None, "evals": [], "stopped": None}
        self.bad = 0

    def _write(self):
        self.save_dir.mkdir(parents=True, exist_ok=True)
        (self.save_dir / "safe_train.json").write_text(json.dumps(self.state, indent=1))

    def _stop(self, agent, reason: str):
        if self.state["stopped"] is None:
            self.state["stopped"] = reason
            print(f"[train_safe] DETENIDO: {reason}", flush=True)
            self._write()
        agent._should_stop = True

    def on_fit_start(self, agent):
        if FREEZE_NORM:
            n = 0
            for m in agent.model.modules():
                if hasattr(m, "_freeze_running"):
                    m._freeze_running = True
                    n += 1
            print(f"[train_safe] normalización congelada en {n} módulos", flush=True)
            self.state["frozen_normalizers"] = n
        if WARMUP_EPOCHS > 0 and agent.current_epoch < WARMUP_EPOCHS:
            self.frozen_lrs = [g["lr"] for g in agent.actor_optimizer.param_groups]
            for g in agent.actor_optimizer.param_groups:
                g["lr"] = 0.0
            print(f"[train_safe] actor congelado {WARMUP_EPOCHS} épocas (calentamiento del crítico)", flush=True)

    def before_play_steps(self, agent):
        if self.t0 is None:
            self.t0 = time.time()
        if self.frozen_lrs is not None and agent.current_epoch >= WARMUP_EPOCHS:
            for g, lr in zip(agent.actor_optimizer.param_groups, self.frozen_lrs):
                g["lr"] = lr
            self.frozen_lrs = None
            print(f"[train_safe] época {agent.current_epoch}: actor descongelado", flush=True)
        if (time.time() - self.t0) / 60 >= TRAIN_MIN:
            self._stop(agent, f"tiempo: {TRAIN_MIN:.0f} min de entrenamiento")

    def on_eval_end(self, agent):
        score = getattr(agent.evaluator, "_last_score", None)
        if score is None:
            return
        score = float(score)
        ep = int(agent.current_epoch)
        self.state["evals"].append({"epoch": ep, "score": round(score, 4)})
        if self.state["start_score"] is None:
            self.state["start_score"] = score
        if self.state["best_score"] is None or score >= self.state["best_score"]:
            self.state["best_score"] = score
        print(f"[train_safe] eval época {ep}: {score:.3f} (inicio {self.state['start_score']:.3f}, "
              f"mejor {self.state['best_score']:.3f})", flush=True)
        if ep >= WARMUP_EPOCHS and score < self.state["start_score"] - MARGIN:
            self.bad += 1
            if self.bad >= PATIENCE:
                self._stop(agent, f"empeoró: {score:.3f} < inicio {self.state['start_score']:.3f} - {MARGIN} "
                                  f"en {PATIENCE} evaluaciones seguidas")
        else:
            self.bad = 0
        self._write()


def main() -> None:
    argv = sys.argv[1:]
    sys.path.insert(0, os.getcwd())  # la receta importa examples.* desde la raíz de ProtoMotions
    name = argv[argv.index("--experiment-name") + 1] if "--experiment-name" in argv else "default"
    safe = SafeTrain(Path("results") / name)

    # Isaac Sim tiene que importarse antes que torch (igual que protomotions/train_agent.py).
    from protomotions.launch.startup import simulator_from_argv
    from protomotions.utils.simulator_imports import import_simulator_before_torch

    app_launcher = import_simulator_before_torch(simulator_from_argv(argv))

    import lightning.fabric

    if os.environ.get("FORCE_CPU") == "1":  # prueba local en el Mac (sin CUDA): Fabric en CPU
        orig_init = lightning.fabric.Fabric.__init__

        def cpu_init(self, *a, **k):
            k["accelerator"] = "cpu"
            orig_init(self, *a, **k)

        lightning.fabric.Fabric.__init__ = cpu_init
    from protomotions.agents.evaluators.base_evaluator import BaseEvaluator

    orig_eval = BaseEvaluator.evaluate

    def evaluate(self):
        result = orig_eval(self)
        self._last_score = getattr(result, "score", None)
        return result

    BaseEvaluator.evaluate = evaluate
    orig_call = lightning.fabric.Fabric.call

    def call(self, hook_name, *args, **kwargs):
        out = orig_call(self, hook_name, *args, **kwargs)
        fn = getattr(safe, hook_name, None)
        if fn is not None and args:
            fn(args[0])
        return out

    lightning.fabric.Fabric.call = call
    from protomotions.launch.training import run

    try:
        run(argv, app_launcher)
    finally:
        if safe.state["stopped"] is None:
            safe.state["stopped"] = "terminó normalmente"
        safe._write()


if __name__ == "__main__":
    from protomotions.launch.startup import run_reporting_failures

    run_reporting_failures(main)
