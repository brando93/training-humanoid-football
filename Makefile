# Todo comando que toque AWS pasa por check-account primero.
export AWS_PROFILE := humanoid
export AWS_REGION := us-east-1

.PHONY: help login check-account scan hooks

help:
	@echo "make login          - inicia sesión SSO (perfil humanoid)"
	@echo "make check-account  - verifica que el perfil apunte a la cuenta del proyecto"
	@echo "make scan           - busca secretos en todo el historial con gitleaks"
	@echo "make hooks          - instala el hook pre-commit de gitleaks"

login:
	aws sso login --profile $(AWS_PROFILE)

check-account:
	@./scripts/check-aws-account.sh

scan:
	gitleaks git --redact --verbose .

hooks:
	@cp scripts/pre-commit.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
	@echo "Hook pre-commit instalado (gitleaks)."
