# Todo comando que toque AWS pasa por check-account primero.
export AWS_PROFILE := humanoid
export AWS_REGION := us-east-1

.PHONY: help login check-account scan hooks ami ami-validate ami-cleanup

help:
	@echo "make login          - inicia sesión SSO (perfil humanoid)"
	@echo "make check-account  - verifica que el perfil apunte a la cuenta del proyecto"
	@echo "make scan           - busca secretos en todo el historial con gitleaks"
	@echo "make hooks          - instala el hook pre-commit de gitleaks"
	@echo "make ami-validate   - valida la plantilla de Packer"
	@echo "make ami            - construye la AMI de entrenamiento (~\$$0,20 por build)"
	@echo "make ami-cleanup    - borra AMIs viejas y sus snapshots (conserva la más reciente)"

login:
	aws sso login --profile $(AWS_PROFILE)

check-account:
	@./scripts/check-aws-account.sh

scan:
	gitleaks git --redact --verbose .

hooks:
	@cp scripts/pre-commit.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
	@echo "Hook pre-commit instalado (gitleaks)."

ami-validate:
	cd infra/packer && packer init . && packer fmt -check . && packer validate .

ami: check-account ami-validate
	@command -v session-manager-plugin >/dev/null || { echo "Falta session-manager-plugin: brew install --cask session-manager-plugin"; exit 1; }
	cd infra/packer && packer build -timestamp-ui .

ami-cleanup: check-account
	./infra/packer/scripts/cleanup-old-amis.sh 1
