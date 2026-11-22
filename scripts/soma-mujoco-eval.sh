#!/usr/bin/env bash
# Compuerta de MuJoCo en el Mac: evalúa el tracker Anatomical SOMA preentrenado sobre los clips de ejemplo,
# con física MuJoCo en CPU (sin GPU). Es la misma física que correrá dentro de Unreal.
#
# Requisitos (una vez): ver phase0_basics/README.md → "Entorno local único".
# Uso: make soma-mujoco-eval
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
PM="$REPO/third_party/ProtoMotions"
PY="$REPO/phase0_basics/.venv/bin/python"
CKPT="data/pretrained_models/motion_tracker/anatomic_soma_bones_fsq/inference_last.ckpt"
MOTIONS="data/motion_for_trackers/anatomic_soma_bones_seed_mini.pt"
LOG="$REPO/third_party/soma-mujoco-eval.log"

[[ -x "$PY" ]] || { echo "Falta el entorno local: cd phase0_basics && uv sync --group protomotions" >&2; exit 1; }
[[ -f "$PM/$CKPT" ]] || { echo "Falta el checkpoint: ver phase0_basics/README.md (git lfs pull)" >&2; exit 1; }
if head -c 64 "$PM/$CKPT" | grep -q "git-lfs.github.com/spec"; then
  echo "El checkpoint es un puntero de Git LFS sin descargar: corre git lfs pull" >&2; exit 1
fi

cd "$PM"
"$PY" protomotions/inference_agent.py --simulator mujoco --checkpoint "$CKPT" \
  --motion-file "$MOTIONS" --num-envs 1 --headless --full-eval 2>&1 | tee "$LOG"
echo
echo "Resumen:"
grep -E 'eval/(success_rate|gt_error/mean|gr_error/mean|max_joint_error/mean|high_jerk_frame_percentage_mean)|Overall Score' "$LOG"
