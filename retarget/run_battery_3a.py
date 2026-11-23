"""Batería 3a: ¿el cuerpo de Anatomical SOMA puede hacer cada función básica del futbolista?

Para cada habilidad de configs/skills_cmu.yaml:
  1. Empaqueta sus clips retargeteados (data/cmu_motions/<habilidad>/*.motion) en un MotionLib.
  2. Evalúa el tracker preentrenado en MuJoCo (CPU, la misma física que irá en Unreal).
  3. Guarda las métricas y escribe un reporte en docs/reports/battery_3a.md.

Criterio de la Fase 3a (docs/plan.md): ≥ 90% de los clips sin caída y error de posición medio < 10 cm.

Uso (desde la raíz del repo; antes: retarget/cmu_to_anatomic_soma.py):
  phase0_basics/.venv/bin/python retarget/run_battery_3a.py
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PM = Path(os.environ.get("PM_ROOT", REPO / "third_party" / "ProtoMotions"))  # en la instancia: /opt/humanoid/ProtoMotions
PY = Path(os.environ.get("PY_BIN", REPO / "phase0_basics" / ".venv" / "bin" / "python"))  # en la instancia: /opt/humanoid/venv/bin/python
# CHECKPOINT=ruta/al/tracker.ckpt para medir uno propio (Fase 3b); relativo a third_party/ProtoMotions o absoluto.
CKPT = os.environ.get("CHECKPOINT", "data/pretrained_models/motion_tracker/anatomic_soma_bones_fsq/inference_last.ckpt")
MOTIONS = Path(os.environ.get("MOTIONS_DIR", REPO / "data" / "cmu_motions")).resolve()
METRICS = ["success_rate", "gt_error/mean", "gt_error/max", "gr_error/mean", "high_jerk_frame_percentage_mean", "num_evaluated"]


def run(cmd: list[str]) -> str:
    r = subprocess.run(cmd, cwd=PM, capture_output=True, text=True)
    return r.stdout + r.stderr


def evaluate(skill: str) -> dict:
    lib = MOTIONS / f"{skill}.pt"
    run([str(PY), "protomotions/components/motion_lib.py", "--motion-path", str(MOTIONS / skill), "--output-file", str(lib)])
    out = run([str(PY), "protomotions/inference_agent.py", "--simulator", "mujoco", "--checkpoint", CKPT,
               "--motion-file", str(lib), "--num-envs", "1", "--headless", "--full-eval"])
    vals = {}
    for k in METRICS:
        m = re.search(rf"eval/{re.escape(k)}: ([0-9.eE+-]+)", out)
        vals[k] = float(m.group(1)) if m else None
    (MOTIONS / f"{skill}.eval.log").write_text(out)
    return vals


def main() -> None:
    from concurrent.futures import ThreadPoolExecutor, as_completed

    skills = sorted(p.name for p in MOTIONS.iterdir() if p.is_dir() and any(p.glob("*.motion")))
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 4  # cada evaluación usa ~1 núcleo
    results = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(evaluate, s): s for s in skills}
        for n, fut in enumerate(as_completed(futures), 1):
            skill = futures[fut]
            results[skill] = fut.result()
            v = results[skill]
            print(f"[{n}/{len(skills)}] {skill:22} éxito={v['success_rate']} error_pos_medio={v['gt_error/mean']}", flush=True)
    results = dict(sorted(results.items()))

    retarget = json.loads((MOTIONS / "retarget_report.json").read_text()) if (MOTIONS / "retarget_report.json").exists() else {}
    lines = [
        f"# Batería 3a — funciones básicas del futbolista en MuJoCo ({date.today().isoformat()})",
        "",
        "Tracker preentrenado de Anatomical SOMA (ProtoMotions), física MuJoCo en CPU (Mac), clips de CMU",
        "Motion Capture retargeteados con `retarget/cmu_to_anatomic_soma.py`.",
        "Criterio: ≥ 90% de clips sin caída y error de posición medio < 10 cm.",
        "",
        "| Habilidad | Clips | Éxito | Error pos. medio | Error pos. máx. | Error rot. medio | Jerk alto | ¿Pasa? |",
        "|---|---|---|---|---|---|---|---|",
    ]
    passed = 0
    for skill, v in results.items():
        ok = v["success_rate"] is not None and v["success_rate"] >= 0.9 and (v["gt_error/mean"] or 1) < 0.10
        passed += ok
        fmt = lambda x, mul=1, suf="": "—" if x is None else f"{x*mul:.1f}{suf}"  # noqa: E731
        lines.append(
            f"| {skill} | {int(v['num_evaluated'] or 0)} | {fmt(v['success_rate'], 100, '%')} | {fmt(v['gt_error/mean'], 100, ' cm')} "
            f"| {fmt(v['gt_error/max'], 100, ' cm')} | {fmt(v['gr_error/mean'], 57.2958, '°')} | {fmt(v['high_jerk_frame_percentage_mean'], 1, '%')} | {'✅' if ok else '❌'} |"
        )
    lines += ["", f"**Resultado: {passed}/{len(results)} habilidades pasan.**", ""]
    if retarget:
        ik = [v["ik_rmse_cm_mean"] for v in retarget.values()]
        sl = [v["foot_slide_cm_s"] for v in retarget.values() if v.get("foot_slide_cm_s") is not None]
        lines += [
            "## Calidad del retargeting",
            f"- Clips: {len(retarget)}. Error medio de la cinemática inversa: {sum(ik)/len(ik):.1f} cm (máx. {max(ik):.1f} cm).",
            f"- Deslizamiento de pies en contacto: {sum(sl)/len(sl):.1f} cm/s de media." if sl else "- Deslizamiento de pies: sin contactos detectados.",
        ]
    report = REPO / "docs" / "reports" / "battery_3a.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n")
    (MOTIONS / "battery_3a.json").write_text(json.dumps(results, indent=2))
    print(f"\nReporte: {report}")


if __name__ == "__main__":
    sys.exit(main())
