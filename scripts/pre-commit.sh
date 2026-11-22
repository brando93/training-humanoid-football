#!/usr/bin/env bash
# Hook pre-commit: bloquea el commit si gitleaks encuentra un secreto en lo que está en stage.
# Se instala con: make hooks
set -euo pipefail

if ! command -v gitleaks >/dev/null 2>&1; then
  echo "gitleaks no está instalado. Instálalo con: brew install gitleaks" >&2
  exit 1
fi

gitleaks git --staged --redact --no-banner
