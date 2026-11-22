#!/usr/bin/env bash
# Verifica que las credenciales activas apunten a la cuenta personal del proyecto.
# Evita usar por error un perfil de trabajo. Lo llaman el Makefile y los scripts de infra.
set -euo pipefail

EXPECTED_ACCOUNT="611606529792"
PROFILE="${AWS_PROFILE:-humanoid}"

if ! actual="$(aws sts get-caller-identity --profile "$PROFILE" --query Account --output text 2>/dev/null)"; then
  echo "ERROR: no hay sesión válida para el perfil '$PROFILE'." >&2
  echo "Corre: aws sso login --profile $PROFILE" >&2
  exit 1
fi

if [[ "$actual" != "$EXPECTED_ACCOUNT" ]]; then
  echo "ERROR: el perfil '$PROFILE' apunta a la cuenta $actual, no a $EXPECTED_ACCOUNT. Abortando." >&2
  exit 1
fi

echo "OK: perfil '$PROFILE' -> cuenta $actual"
