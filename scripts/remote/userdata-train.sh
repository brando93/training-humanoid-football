#!/bin/bash
# User data de una corrida diaria (lo pasa scripts/launch-trainer.sh --run). Corre como root al arrancar.
shutdown -h +90 "humanoid: tiempo máximo alcanzado"   # seguro de costo; terminar al apagar
export AWS_DEFAULT_REGION=us-east-1
B=humanoid-artifacts-611606529792
aws s3 cp "s3://$B/${CODE_KEY:-code/latest.tar.gz}" /tmp/c.tgz --only-show-errors \
  && mkdir -p /tmp/c && tar -xzf /tmp/c.tgz -C /tmp/c scripts/remote/train-3b.sh \
  && CODE_KEY="${CODE_KEY:-code/latest.tar.gz}" bash /tmp/c/scripts/remote/train-3b.sh
shutdown -h now "humanoid: corrida terminada"
