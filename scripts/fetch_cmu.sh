#!/usr/bin/env bash
# Baja de CMU Motion Capture (ASF/AMC) los trials listados en configs/skills_cmu.yaml.
# Destino: data/cmu_raw/ (ignorado por git). Uso: ./scripts/fetch_cmu.sh
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$REPO/data/cmu_raw"; mkdir -p "$OUT"
trials=$(grep -oE '[0-9]+_[0-9]+' "$REPO/configs/skills_cmu.yaml" | sort -u)
for t in $trials; do
  s="${t%%_*}"; s_dir="$s"
  [[ -f "$OUT/$s.asf" ]] || curl -sSfL --retry 3 -o "$OUT/$s.asf" "http://mocap.cs.cmu.edu/subjects/$s_dir/$s.asf"
  [[ -f "$OUT/$t.amc" ]] || curl -sSfL --retry 3 -o "$OUT/$t.amc" "http://mocap.cs.cmu.edu/subjects/$s_dir/$t.amc"
done
echo "Trials: $(echo "$trials" | wc -w | tr -d ' ') | Archivos en $OUT: $(find "$OUT" -type f | wc -l | tr -d ' ') | $(du -sh "$OUT" | cut -f1)"
