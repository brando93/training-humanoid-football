#!/usr/bin/env bash
# Baja de CMU Motion Capture (ASF/AMC) los trials de configs/skills_cmu.yaml y configs/training_extra_cmu.yaml.
# Destino: data/cmu_raw/ (ignorado por git). Uso: ./scripts/fetch_cmu.sh
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$REPO/data/cmu_raw"; mkdir -p "$OUT"
trials=$(grep -hoE '\b[0-9]+_[0-9]+\b' "$REPO/configs/skills_cmu.yaml" "$REPO/configs/training_extra_cmu.yaml" | sort -u)
for t in $trials; do
  s="${t%%_*}"; s_dir=$(printf "%02d" "$s"); n="${t#*_}"  # la web usa 07/07_01; localmente 7_01
  [[ -f "$OUT/$s.asf" ]] || curl -sSfL --retry 3 -o "$OUT/$s.asf" "http://mocap.cs.cmu.edu/subjects/$s_dir/$s_dir.asf"
  [[ -f "$OUT/$t.amc" ]] || curl -sSfL --retry 3 -o "$OUT/$t.amc" "http://mocap.cs.cmu.edu/subjects/$s_dir/${s_dir}_$n.amc"
done
echo "Trials: $(echo "$trials" | wc -w | tr -d ' ') | Archivos en $OUT: $(find "$OUT" -type f | wc -l | tr -d ' ') | $(du -sh "$OUT" | cut -f1)"
