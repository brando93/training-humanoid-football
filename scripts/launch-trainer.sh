#!/usr/bin/env bash
# Lanza UNA instancia GPU spot con el launch template humanoid-trainer, probando zonas hasta encontrar capacidad.
# La plantilla ya trae: spot one-time, terminar al apagar, apagado forzado a los 90 min, disco que se borra.
# Uso: scripts/launch-trainer.sh g4dn.2xlarge   -> imprime el instance-id
set -euo pipefail
TYPE="${1:?tipo de instancia, ej. g4dn.2xlarge}"
P=(--profile humanoid --region us-east-1)
"$(dirname "$0")/check-aws-account.sh" >/dev/null
running=$(aws ec2 describe-instances "${P[@]}" --filters Name=tag:Name,Values=humanoid-trainer \
  Name=instance-state-name,Values=pending,running --query 'length(Reservations[].Instances[])' --output text)
[[ "$running" == "0" ]] || { echo "Ya hay $running instancia(s) humanoid-trainer corriendo; no lanzo otra." >&2; exit 1; }
ERR=$(mktemp); trap 'rm -f "$ERR"' EXIT
SG=$(aws ec2 describe-security-groups "${P[@]}" --filters Name=group-name,Values=humanoid-trainer --query 'SecurityGroups[0].GroupId' --output text)
# Zonas ordenadas por precio spot actual de este tipo.
mapfile -t AZS < <(aws ec2 describe-spot-price-history "${P[@]}" --instance-types "$TYPE" --product-descriptions Linux/UNIX \
  --start-time "$(date -u +%Y-%m-%dT%H:%M:%S)" --query 'SpotPriceHistory[].[SpotPrice,AvailabilityZone]' --output text | sort -n | awk '{print $2}')
for az in "${AZS[@]}"; do
  SUB=$(aws ec2 describe-subnets "${P[@]}" --filters "Name=tag:Name,Values=humanoid-public-$az" --query 'Subnets[0].SubnetId' --output text)
  [[ "$SUB" == "None" ]] && continue
  # shellcheck disable=SC2016  # $Latest es literal: la versión más reciente de la plantilla
  if id=$(aws ec2 run-instances "${P[@]}" --launch-template 'LaunchTemplateName=humanoid-trainer,Version=$Latest' \
      --instance-type "$TYPE" --network-interfaces "DeviceIndex=0,SubnetId=$SUB,Groups=$SG,AssociatePublicIpAddress=true,DeleteOnTermination=true" \
      --query 'Instances[0].InstanceId' --output text 2>"$ERR"); then
    echo "Lanzada $id ($TYPE) en $az" >&2; echo "$id"; exit 0
  fi
  echo "$az: $(grep -oE '\(([A-Za-z]+)\)' "$ERR" | head -1)" >&2
done
echo "Sin capacidad spot de $TYPE en ninguna zona con subred." >&2; exit 1
