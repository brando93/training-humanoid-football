#!/usr/bin/env bash
# Conserva solo las N AMIs humanoid-trainer más recientes y borra las demás con sus snapshots.
# Cada AMI vieja cuesta ~$3/mes en snapshots, así que por defecto se conserva solo 1.
# Uso: ./cleanup-old-amis.sh [N]   (pide confirmación antes de borrar)
# Compatible con el bash 3.2 de macOS.
set -euo pipefail

KEEP="${1:-1}"
export AWS_PROFILE="${AWS_PROFILE:-humanoid}" AWS_REGION="${AWS_REGION:-us-east-1}"

all=$(aws ec2 describe-images --owners self \
  --filters "Name=name,Values=humanoid-trainer-*" \
  --query 'sort_by(Images,&CreationDate)[].ImageId' --output text | tr '\t' '\n' | sed '/^$/d')
total=$(printf '%s\n' "$all" | sed '/^$/d' | wc -l | tr -d ' ')
drop=$(( total > KEEP ? total - KEEP : 0 ))

if [[ "$drop" -eq 0 ]]; then
  echo "Nada que borrar ($total AMIs, se conservan las $KEEP más recientes)."
  exit 0
fi

old=$(printf '%s\n' "$all" | head -n "$drop")
echo "Se borrarán estas AMIs y sus snapshots:"
echo "$old"
read -r -p "¿Confirmas? (escribe 'si'): " ok
[[ "$ok" == "si" ]] || { echo "Cancelado."; exit 1; }

for ami in $old; do
  snaps=$(aws ec2 describe-images --image-ids "$ami" --query 'Images[0].BlockDeviceMappings[].Ebs.SnapshotId' --output text)
  aws ec2 deregister-image --image-id "$ami"
  for s in $snaps; do aws ec2 delete-snapshot --snapshot-id "$s"; done
  echo "Borrada $ami ($snaps)"
done
