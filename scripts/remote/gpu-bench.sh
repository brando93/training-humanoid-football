#!/usr/bin/env bash
# Prueba de humo + velocidad en la instancia GPU (se ejecuta allá por SSM).
# Uso: gpu-bench.sh <num_envs> <iteraciones>
set -uo pipefail
N="${1:-2048}"; IT="${2:-30}"
BUCKET=humanoid-artifacts-611606529792
TAG="$(date -u +%Y%m%dT%H%M%SZ)-$(curl -s -H "X-aws-ec2-metadata-token: $(curl -s -X PUT http://169.254.169.254/latest/api/token -H 'X-aws-ec2-metadata-token-ttl-seconds: 60')" http://169.254.169.254/latest/meta-data/instance-type)"
LOG=/opt/humanoid/bench-$TAG.log
exec > >(tee "$LOG") 2>&1
echo "== $TAG num_envs=$N iteraciones=$IT"
# shellcheck disable=SC1091  # existe solo en la AMI
source /opt/humanoid/env.sh
echo "EULA: ${OMNI_KIT_ACCEPT_EULA:-NO}"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
aws s3 cp "s3://$BUCKET/data/cmu_soma_all.pt" /opt/humanoid/cmu_soma_all.pt --only-show-errors
cd "$PROTOMOTIONS_ROOT" || exit 1
start=$(date +%s)
timeout 45m python protomotions/train_agent.py --robot-name anatomic_soma --simulator isaaclab \
  --experiment-path examples/experiments/mimic/anatomical_soma_fsq_mimic.py \
  --motion-file /opt/humanoid/cmu_soma_all.pt --num-envs "$N" --batch-size "$N" \
  --experiment-name "bench_$N" --headless --training-max-iterations "$IT"
rc=$?
echo "== código de salida: $rc | segundos totales: $(( $(date +%s) - start ))"
nvidia-smi --query-gpu=memory.used --format=csv
aws s3 cp "$LOG" "s3://$BUCKET/logs/bench/" --only-show-errors
exit $rc
