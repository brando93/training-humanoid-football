#!/usr/bin/env bash
# Corrida de la Fase 3b en la instancia GPU (la lanza user data; ver scripts/remote/userdata-train.sh).
#  1. Parte del último modelo APROBADO (s3://.../checkpoints/3b/approved/, el que Brandon aceptó con merge);
#     si no hay, arranca del tracker de NVIDIA (warm start).
#  2. Entrena TRAIN_MIN minutos con los 55 clips de CMU (last.ckpt se guarda cada ~2 min).
#  3. Mide en MuJoCo (5 corridas por clip), graba un clip por habilidad y arma el reporte.
#  4. Sube candidato, reporte y videos a S3. Un workflow de GitHub abre el PR para la review.
# La instancia nunca toca GitHub. El apagado forzado (90 min) y el freno de costos siguen activos.
set -uo pipefail
TRAIN_MIN="${TRAIN_MIN:-35}"  # arranque ~13 + entrenar 35 + medir ~25 + videos ~3 < 90 min del apagado forzado
BUCKET=humanoid-artifacts-611606529792
RUN_ID="${RUN_ID:-$(date -u +%Y-%m-%d-%H%M)}"
ROOT=/opt/humanoid
REPO="$ROOT/repo"
LOG="$ROOT/run-$RUN_ID.log"
exec > >(tee -a "$LOG") 2>&1
s3() { aws s3 "$@" --only-show-errors; }
finish() {  # pase lo que pase, el log llega a S3
  s3 cp "$LOG" "s3://$BUCKET/logs/runs/$RUN_ID.log"
}
trap finish EXIT
echo "== corrida $RUN_ID | entrenamiento $TRAIN_MIN min | $(date -u)"
# shellcheck disable=SC1091  # existe solo en la AMI
source "$ROOT/env.sh"
[[ "${OMNI_KIT_ACCEPT_EULA:-}" == "YES" ]] || { echo "EULA de Isaac Sim no aceptada (SSM)"; exit 1; }

echo "== código y datos"
mkdir -p "$REPO" && s3 cp "s3://$BUCKET/${CODE_KEY:-code/latest.tar.gz}" /tmp/code.tar.gz && tar -xzf /tmp/code.tar.gz -C "$REPO"
s3 cp "s3://$BUCKET/data/cmu_soma_all.pt" "$ROOT/cmu_soma_all.pt"
s3 sync "s3://$BUCKET/data/cmu_motions/" "$REPO/data/cmu_motions/"

cd "$PROTOMOTIONS_ROOT" || exit 1
SAVE=results/fase3b
rm -rf "$SAVE"; mkdir -p "$SAVE"
if aws s3 ls "s3://$BUCKET/checkpoints/3b/approved/last.ckpt" >/dev/null 2>&1; then
  echo "== reanuda desde el último modelo aprobado"
  s3 sync "s3://$BUCKET/checkpoints/3b/approved/" "$SAVE/"
  PREV="aprobado"
  WARM=()
else
  echo "== warm start desde el tracker de NVIDIA"
  PREV="nvidia"
  WARM=(--checkpoint data/pretrained_models/motion_tracker/anatomic_soma_bones_fsq/inference_last.ckpt)
fi

echo "== entrena $TRAIN_MIN min"
t0=$(date +%s)
timeout --signal=INT --kill-after=60 "${TRAIN_MIN}m" python protomotions/train_agent.py --robot-name anatomic_soma \
  --simulator isaaclab --experiment-path examples/experiments/mimic/anatomical_soma_fsq_mimic.py \
  --motion-file "$ROOT/cmu_soma_all.pt" --num-envs 2048 --batch-size 2048 \
  --experiment-name fase3b --headless "${WARM[@]}"
echo "== entrenamiento terminó (código $?) en $(( ($(date +%s) - t0) / 60 )) min"
[[ -f "$SAVE/last.ckpt" ]] || { echo "No hay last.ckpt: no se sube nada"; exit 1; }
s3 sync "$SAVE/" "s3://$BUCKET/checkpoints/3b/candidates/$RUN_ID/" --exclude "*epoch_*"

echo "== mide en MuJoCo y graba clips"
export PY_BIN="$ROOT/venv/bin/python" PM_ROOT="$PROTOMOTIONS_ROOT" MUJOCO_GL=egl
export CHECKPOINT="$PROTOMOTIONS_ROOT/$SAVE/last.ckpt"
cd "$REPO" || exit 1
WORKERS=7 REPEATS=5 "$PY_BIN" retarget/eval_repeat.py "repeat_$RUN_ID"
# Para comparar: medición del modelo aprobado anterior (o la base del tracker de NVIDIA).
prev_run=$(aws s3 cp "s3://$BUCKET/checkpoints/3b/approved.json" - 2>/dev/null | "$PY_BIN" -c "import json,sys;print(json.load(sys.stdin)['run_id'])" 2>/dev/null || echo 2026-11-22-base)
PREV_ARGS=()
s3 cp "s3://$BUCKET/reports/runs/$prev_run/report/eval.json" /tmp/prev_eval.json && PREV_ARGS=(--prev-eval /tmp/prev_eval.json)
MEDIA="$ROOT/media"; rm -rf "$MEDIA"
steps=$("$PY_BIN" -c "import torch;print(torch.load('$CHECKPOINT',map_location='cpu',weights_only=False)['step_count'])" 2>/dev/null || echo "?")
WORKERS=7 "$PY_BIN" retarget/make_run_report.py --eval "data/cmu_motions/repeat_$RUN_ID.json" --run-id "$RUN_ID" \
  --label "Fase 3b: ajuste fino del tracker con clips CMU" --media-dir "$MEDIA" \
  --cost "${COST:-≈ \$1,10 (g6.2xlarge spot, ~90 min)}" \
  --notes "Parte de: $PREV (comparado con la corrida $prev_run). Entrenó $TRAIN_MIN min (pasos acumulados: $steps)." \
  "${PREV_ARGS[@]}"
cp "data/cmu_motions/repeat_$RUN_ID.json" "reports/runs/$RUN_ID/eval.json"

echo "== sube reporte y videos"
s3 sync "reports/runs/$RUN_ID/" "s3://$BUCKET/reports/runs/$RUN_ID/report/"
s3 sync "$MEDIA/runs/$RUN_ID/" "s3://$BUCKET/reports/runs/$RUN_ID/media/"
date -u +%FT%TZ | aws s3 cp - "s3://$BUCKET/reports/runs/$RUN_ID/DONE" --only-show-errors
echo "== listo $(date -u). Se apaga."
