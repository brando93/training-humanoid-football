#!/usr/bin/env bash
# Corrida de la Fase 3b en la instancia GPU (la lanza user data; ver scripts/remote/userdata-train.sh).
#  1. Parte del último modelo APROBADO (s3://.../checkpoints/3b/approved/, el que Brandon aceptó con merge);
#     si no hay, arranca del tracker de NVIDIA (warm start).
#  2. Entrena TRAIN_MIN minutos con los clips de entrenamiento (data/cmu_soma_train.pt: sin los clips rotos).
#  3. Si mejoró, sube el candidato y marca TRAINED. Se apaga: la GPU solo entrena.
#  4. La medición en MuJoCo y los clips son CPU: los hace GitHub Actions (measure-run.yml, $0), que deja DONE;
#     luego run-pr.yml abre el PR para la review.
# La instancia nunca toca GitHub. El apagado forzado (90 min) y el freno de costos siguen activos.
set -uo pipefail
TRAIN_MIN="${TRAIN_MIN:-35}"  # arranque ~13 + entrenar 35 + subir ~2 = ~50 min, lejos del apagado forzado (90)
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
TRAIN_SET="${TRAIN_SET:-cmu_soma_train_v2.pt}"  # retarget/pack_training_set.py (v2: 208 clips, 2026-11-24)
s3 cp "s3://$BUCKET/data/$TRAIN_SET" "$ROOT/train_set.pt"
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

echo "== entrena $TRAIN_MIN min (contados desde la primera época) con training/train_safe.py"
# Seguro: normalización congelada, crítico calentado con el actor congelado, tasa baja (training/fase3b_finetune.py),
# evaluación cada FT_EVAL_EVERY épocas, freno si empeora y límite de tiempo. timeout es solo el respaldo duro.
t0=$(date +%s)
TRAIN_MIN="$TRAIN_MIN" timeout --signal=INT --kill-after=60 "$((TRAIN_MIN + 15))m" python "$REPO/training/train_safe.py" \
  --robot-name anatomic_soma --simulator isaaclab --experiment-path "$REPO/training/fase3b_finetune.py" \
  --motion-file "$ROOT/train_set.pt" --num-envs 2048 --batch-size 2048 \
  --experiment-name fase3b --headless "${WARM[@]}"
echo "== entrenamiento terminó (código $?) en $(( ($(date +%s) - t0) / 60 )) min"
cat "$SAVE/safe_train.json" 2>/dev/null
[[ -f "$SAVE/score_based.ckpt" ]] || { echo "No hay score_based.ckpt: no se sube nada"; exit 1; }
if [[ "${RUN_MODE:-}" == "preflight" ]]; then
  # Prueba corta en GPU: solo la curva de entrenamiento y el KL; sin medir, sin videos, sin candidato.
  python - "$SAVE" > "$ROOT/preflight.txt" <<'PYEOF'
import glob, json, sys
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
d = sys.argv[1]
print(json.dumps(json.load(open(f"{d}/safe_train.json")), indent=1))
ea = EventAccumulator(glob.glob(f"{d}/lightning_logs/*/events*")[0]); ea.Reload()
for t in ["actor/approx_kl", "actor/clip_frac", "losses/critic_loss", "critic/explained_variance", "rewards/task_rewards"]:
    v = [round(x.value, 4) for x in ea.Scalars(t)]
    print(f"{t}: {v[:3]} ... {v[-3:]} (max {max(v)})")
PYEOF
  cat "$ROOT/preflight.txt"
  s3 cp "$ROOT/preflight.txt" "s3://$BUCKET/reports/preflight/$RUN_ID.txt"
  echo "== prueba corta terminada"; exit 0
fi
# El candidato es el MEJOR modelo de la corrida, no el último.
cp "$SAVE/score_based.ckpt" "$SAVE/last.ckpt"
cp "$SAVE/inference_score_based.ckpt" "$SAVE/inference_last.ckpt" 2>/dev/null || true
improved=$(python -c "import json;s=json.load(open('$SAVE/safe_train.json'));print(int(s['best_score'] is not None and s['start_score'] is not None and s['best_score'] > s['start_score'] + 1e-6))")
s3 cp "$SAVE/safe_train.json" "s3://$BUCKET/reports/runs/$RUN_ID/safe_train.json"
if [[ "$improved" != "1" ]]; then
  echo "== SIN MEJORA en la evaluación interna: no se mide, no se graba, no hay PR. Se apaga para ahorrar."
  date -u +%FT%TZ | aws s3 cp - "s3://$BUCKET/reports/runs/$RUN_ID/NO_IMPROVEMENT" --only-show-errors
  exit 0
fi
s3 sync "$SAVE/" "s3://$BUCKET/checkpoints/3b/candidates/$RUN_ID/" --exclude "*epoch_*" --exclude "score_based.ckpt" --exclude "inference_score_based.ckpt"

# Para la medición: con qué modelo comparar (el aprobado del que partió) y cuánto entrenó.
steps=$(python -c "import torch;print(torch.load('$SAVE/last.ckpt',map_location='cpu',weights_only=False)['step_count'])" 2>/dev/null || echo "?")
printf '{"run_id": "%s", "prev": "%s", "train_min": %s, "steps": "%s", "train_set": "%s", "date": "%s"}\n' \
  "$RUN_ID" "$PREV" "$TRAIN_MIN" "$steps" "$TRAIN_SET" "$(date -u +%FT%TZ)" > "$ROOT/trained.json"
s3 cp "$ROOT/trained.json" "s3://$BUCKET/reports/runs/$RUN_ID/TRAINED"
echo "== listo en $(( ($(date +%s) - t0) / 60 )) min desde el inicio del entrenamiento. Se apaga; GitHub Actions mide y graba."
