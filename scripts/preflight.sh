#!/usr/bin/env bash
# Revisión previa ($0, ~3 min en el Mac). Obligatoria antes de lanzar una corrida de GPU si cambió la receta,
# el entrenamiento o el modelo de partida. Comprueba:
#  1. qué trae el checkpoint de partida (actor, crítico, normalización);
#  2. que el entrenamiento seguro arranca, congela, evalúa, frena y guarda el mejor modelo (MuJoCo, CPU);
#  3. que la política NO se deforma en los primeros pasos (KL pequeño) y que la normalización no se mueve.
# Uso: make preflight   (CHECKPOINT=... para otro modelo de partida)
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PM="$REPO/third_party/ProtoMotions"
PY="$REPO/phase0_basics/.venv/bin/python"
CKPT="${CHECKPOINT:-data/pretrained_models/motion_tracker/anatomic_soma_bones_fsq/inference_last.ckpt}"
OUT="$PM/results/preflight"
cd "$PM"

echo "== 1. Checkpoint de partida: $CKPT"
"$PY" - "$CKPT" <<'PYEOF'
import sys, torch
m = torch.load(sys.argv[1], map_location="cpu", weights_only=False)
sd = m["model"]
actor = [k for k in sd if k.startswith("_actor")]
critic = [k for k in sd if k.startswith("_critic")]
norm = [k for k in sd if "running_obs_norm" in k]
print(f"   actor: {len(actor)} tensores | crítico: {len(critic)} | normalización: {len(norm)} | "
      f"optimizadores: {'sí' if any('optimizer' in k for k in m) else 'no'} | pasos previos: {m.get('step_count')}")
if not actor:
    sys.exit("   ERROR: no hay actor")
if not critic:
    print("   AVISO: sin crítico -> el calentamiento del crítico es obligatorio (WARMUP_EPOCHS > 0)")
PYEOF

echo "== 2. Entrenamiento seguro en MuJoCo (CPU, ~2 min)"
rm -rf "$OUT"
LOCAL_SMOKE=1 FORCE_CPU=1 FT_EVAL_EVERY=3 WARMUP_EPOCHS=2 TRAIN_MIN=2 \
  "$PY" "$REPO/training/train_safe.py" --robot-name anatomic_soma --simulator mujoco \
  --experiment-path "$REPO/training/fase3b_finetune.py" --motion-file "$REPO/data/cmu_motions/frenar_en_seco.pt" \
  --num-envs 1 --batch-size 32 --experiment-name preflight --headless --checkpoint "$CKPT" > "$OUT.log" 2>&1 \
  || { tail -20 "$OUT.log"; echo "ERROR: el entrenamiento seguro falló (log: $OUT.log)"; exit 1; }
grep -a "\[train_safe\]" "$OUT.log" | sed 's/^/   /'

echo "== 3. Chequeos"
"$PY" - "$CKPT" "$OUT" <<'PYEOF'
import glob, json, sys, torch
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
ckpt, out = sys.argv[1], sys.argv[2]
st = json.load(open(f"{out}/safe_train.json"))
ok = True
def check(cond, msg):
    global ok
    print(f"   {'OK ' if cond else 'MAL'} {msg}")
    ok &= bool(cond)
check(st["start_score"] is not None and len(st["evals"]) >= 2, f"evaluó {len(st['evals'])} veces (inicio {st['start_score']})")
check(st.get("frozen_normalizers", 0) > 0, f"normalización congelada en {st.get('frozen_normalizers', 0)} módulos")
check(st["best_score"] is not None and st["best_score"] >= st["start_score"], f"mejor puntaje {st['best_score']} >= inicio")
ea = EventAccumulator(glob.glob(f"{out}/lightning_logs/*/events*")[0]); ea.Reload()
kl = max(x.value for x in ea.Scalars("actor/approx_kl"))
check(kl < 0.05, f"KL máximo del actor {kl:.2e} < 0,05 (la corrida fallida tuvo 0,99)")
a = torch.load(ckpt, map_location="cpu", weights_only=False)["model"]
b = torch.load(f"{out}/score_based.ckpt", map_location="cpu", weights_only=False)["model"]
drift = max((a[k].float() - b[k].float()).abs().max().item() for k in a if "running_obs_norm" in k and a[k].dtype.is_floating_point)
check(drift == 0, f"la normalización no se movió (cambio {drift:.1e})")
if not ok:
    sys.exit("REVISIÓN PREVIA FALLÓ: no lanzar en GPU")
print("   Revisión previa OK: se puede lanzar en GPU.")
PYEOF
