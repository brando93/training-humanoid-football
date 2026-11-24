#!/usr/bin/env bash
# Rescata en la Mac ($0) una corrida que entrenó y mejoró pero no alcanzó a medir/grabar en la GPU.
# Mide el candidato ×5 por clip en MuJoCo, graba los clips comparados con el aprobado y sube el reporte
# a S3 con DONE, para que run-pr abra el PR.   Uso: scripts/rescue-run.sh <RUN_ID>
set -euo pipefail
RUN_ID="${1:?RUN_ID}"
P=(--profile humanoid)
BUCKET=s3://humanoid-artifacts-611606529792
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
PY=phase0_basics/.venv/bin/python
D="$REPO/data/run-$RUN_ID"
PREV_CKPT="data/pretrained_models/motion_tracker/anatomic_soma_bones_fsq/inference_last.ckpt" # relativo a ProtoMotions

aws s3 ls "${P[@]}" "$BUCKET/reports/runs/$RUN_ID/DONE" >/dev/null 2>&1 && { echo "Ya tiene DONE"; exit 0; }
mkdir -p "$D"
aws s3 sync "${P[@]}" "$BUCKET/checkpoints/3b/candidates/$RUN_ID/" "$D/" --exclude "last.ckpt" --exclude "lightning_logs/*" --only-show-errors
aws s3 cp "${P[@]}" "$BUCKET/reports/runs/2026-11-22-base/report/eval.json" "$D/prev_eval.json" --only-show-errors

export CHECKPOINT="$D/inference_last.ckpt"
t0=$(date +%s)
echo "== [1/3] medición ×5 por clip (~20 min) $(date +%T)"
REPEATS=5 WORKERS=10 "$PY" retarget/eval_repeat.py "repeat_$RUN_ID"
echo "== [2/3] clips comparados (~10 min) $(date +%T)"
MEDIA="$D/media"; rm -rf "$MEDIA"
WORKERS=8 "$PY" retarget/make_run_report.py --eval "data/cmu_motions/repeat_$RUN_ID.json" --run-id "$RUN_ID" \
  --label "Fase 3b: ajuste fino del tracker con clips CMU" --media-dir "$MEDIA" \
  --cost "≈ \$1,29 (g6.2xlarge spot, 87 min; medición y clips rescatados en la Mac)" \
  --notes "Parte de: tracker NVIDIA (comparado con 2026-11-22-base). Entrenó 35 min; mejor punto en la época 60." \
  --prev-checkpoint "$PREV_CKPT" --train-status "$D/safe_train.json" --prev-eval "$D/prev_eval.json"
cp "data/cmu_motions/repeat_$RUN_ID.json" "reports/runs/$RUN_ID/eval.json"
echo "== [3/3] sube reporte y clips $(date +%T)"
aws s3 sync "${P[@]}" "reports/runs/$RUN_ID/" "$BUCKET/reports/runs/$RUN_ID/report/" --only-show-errors
aws s3 sync "${P[@]}" "$MEDIA/runs/$RUN_ID/" "$BUCKET/reports/runs/$RUN_ID/media/" --only-show-errors
date -u +%FT%TZ | aws s3 cp "${P[@]}" - "$BUCKET/reports/runs/$RUN_ID/DONE" --only-show-errors
echo "== RESCATE LISTO en $(( ($(date +%s)-t0)/60 )) min"
