#!/usr/bin/env bash
# Mide y graba una corrida ya entrenada, fuera de la GPU ($0): la GPU solo entrena (scripts/remote/train-3b.sh deja
# reports/runs/<id>/TRAINED y se apaga). Corre en GitHub Actions (measure-run.yml) o en la Mac como respaldo.
#  1. Baja el candidato y el modelo con el que se compara (el aprobado del que partió, o el tracker de NVIDIA).
#  2. Mide ×5 por clip en MuJoCo, graba los clips lado a lado (aprobado | nuevo) y arma el reporte.
#  3. Sube reporte y clips a S3 y marca DONE; run-pr.yml abre el PR.
# Uso: scripts/measure-run.sh [RUN_ID]   (sin RUN_ID: la corrida más reciente con TRAINED y sin DONE)
set -euo pipefail
BUCKET=s3://humanoid-artifacts-611606529792
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
P=(); [[ -n "${GITHUB_ACTIONS:-}" ]] || P=(--profile humanoid)  # en Actions, OIDC
PY="${PY_BIN:-$REPO/phase0_basics/.venv/bin/python}"
export PY_BIN="$PY" PM_ROOT="${PM_ROOT:-$REPO/third_party/ProtoMotions}"
NVIDIA_CKPT="data/pretrained_models/motion_tracker/anatomic_soma_bones_fsq/inference_last.ckpt"  # relativo a ProtoMotions
s3() { aws s3 "$@" "${P[@]}" --only-show-errors; }

RUN_ID="${1:-}"
if [[ -z "$RUN_ID" ]]; then
  for id in $(aws s3 ls "${P[@]}" "$BUCKET/reports/runs/" | awk '/PRE/ {print $2}' | tr -d / | sort -r); do
    aws s3 ls "${P[@]}" "$BUCKET/reports/runs/$id/TRAINED" >/dev/null 2>&1 || continue
    aws s3 ls "${P[@]}" "$BUCKET/reports/runs/$id/DONE" >/dev/null 2>&1 && continue
    RUN_ID="$id"; break
  done
  [[ -n "$RUN_ID" ]] || { echo "Ninguna corrida entrenada espera medición."; exit 0; }
fi
aws s3 ls "${P[@]}" "$BUCKET/reports/runs/$RUN_ID/DONE" >/dev/null 2>&1 && { echo "$RUN_ID ya tiene DONE"; exit 0; }
echo "== corrida $RUN_ID"
D="$REPO/data/run-$RUN_ID"; mkdir -p "$D"
s3 sync "$BUCKET/checkpoints/3b/candidates/$RUN_ID/" "$D/" --exclude "last.ckpt" --exclude "lightning_logs/*"
[[ -d data/cmu_motions/un_pie ]] || s3 sync "$BUCKET/data/cmu_motions/" data/cmu_motions/
s3 cp "$BUCKET/reports/runs/$RUN_ID/TRAINED" "$D/trained.json" 2>/dev/null || echo '{}' > "$D/trained.json"

# Con qué se compara: el modelo aprobado (del que partió la corrida) o, si no hay, el tracker de NVIDIA.
prev_run=$(aws s3 cp "${P[@]}" "$BUCKET/checkpoints/3b/approved.json" - 2>/dev/null \
  | "$PY" -c "import json,sys;print(json.load(sys.stdin)['run_id'])" 2>/dev/null || true)
if [[ -n "$prev_run" && "$prev_run" != "$RUN_ID" ]]; then
  s3 sync "$BUCKET/checkpoints/3b/approved/" "$D/prev/" --exclude "last.ckpt" --exclude "lightning_logs/*"
  PREV_CKPT="$D/prev/inference_last.ckpt"; PREV_LABEL="modelo aprobado ($prev_run)"
else
  prev_run=2026-11-22-base; PREV_CKPT="$NVIDIA_CKPT"; PREV_LABEL="tracker NVIDIA"
fi
s3 cp "$BUCKET/reports/runs/$prev_run/report/eval.json" "$D/prev_eval.json"

# Costo de la GPU: la instancia del libro del freno de costos que arrancó justo antes de la corrida.
cost=$(aws s3 cp "${P[@]}" "$BUCKET/guard/ledger.json" - 2>/dev/null | "$PY" -c "
import json, sys, datetime as dt
run = dt.datetime.strptime('$RUN_ID', '%Y-%m-%d-%H%M').replace(tzinfo=dt.timezone.utc)
best = None
for i in json.load(sys.stdin)['instances'].values():
    gap = (run - dt.datetime.fromisoformat(i['launch'])).total_seconds()
    if 0 <= gap < 1800 and (best is None or gap < best[0]): best = (gap, i)
print(f\"≈ \${best[1]['cost_usd']:.2f} ({best[1]['type']} spot, {best[1]['hours']*60:.0f} min; medición y clips fuera de la GPU, \$0)\" if best else '—')
" 2>/dev/null || echo "—")
read -r train_min steps < <("$PY" -c "import json;d=json.load(open('$D/trained.json'));print(d.get('train_min','?'),d.get('steps','?'))")

export CHECKPOINT="$D/inference_last.ckpt"
t0=$(date +%s)
echo "== [1/3] medición ×5 por clip $(date +%T)"
REPEATS=5 WORKERS="${WORKERS:-10}" "$PY" retarget/eval_repeat.py "repeat_$RUN_ID"
echo "== [2/3] clips comparados $(date +%T)"
MEDIA="$D/media"; rm -rf "$MEDIA"
WORKERS="${WORKERS:-8}" "$PY" retarget/make_run_report.py --eval "data/cmu_motions/repeat_$RUN_ID.json" --run-id "$RUN_ID" \
  --label "Fase 3b: ajuste fino del tracker con clips CMU" --media-dir "$MEDIA" --cost "$cost" \
  --notes "Parte de: $PREV_LABEL. Entrenó $train_min min (pasos acumulados: $steps)." \
  --prev-checkpoint "$PREV_CKPT" --train-status "$D/safe_train.json" --prev-eval "$D/prev_eval.json"
cp "data/cmu_motions/repeat_$RUN_ID.json" "reports/runs/$RUN_ID/eval.json"
echo "== [3/3] sube reporte y clips $(date +%T)"
s3 sync "reports/runs/$RUN_ID/" "$BUCKET/reports/runs/$RUN_ID/report/"
s3 sync "$MEDIA/runs/$RUN_ID/" "$BUCKET/reports/runs/$RUN_ID/media/"
date -u +%FT%TZ | aws s3 cp "${P[@]}" - "$BUCKET/reports/runs/$RUN_ID/DONE" --only-show-errors
echo "== MEDICIÓN LISTA ($RUN_ID) en $(( ($(date +%s) - t0) / 60 )) min"
echo "run_id=$RUN_ID" >> "${GITHUB_OUTPUT:-/dev/null}"
