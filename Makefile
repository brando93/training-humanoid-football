# Todo comando que toque AWS pasa por check-account primero.
export AWS_PROFILE := humanoid
export AWS_REGION := us-east-1

.PHONY: help login check-account scan hooks ami ami-validate ami-cleanup ami-kill-build local-env soma-mujoco-eval checklist preflight

help:
	@echo "make login          - inicia sesión SSO (perfil humanoid)"
	@echo "make check-account  - verifica que el perfil apunte a la cuenta del proyecto"
	@echo "make scan           - busca secretos en todo el historial con gitleaks"
	@echo "make hooks          - instala el hook pre-commit de gitleaks"
	@echo "make ami-validate   - valida la plantilla de Packer"
	@echo "make ami            - construye la AMI de entrenamiento (~\$$0,20 por build)"
	@echo "make ami-cleanup    - borra AMIs viejas y sus snapshots (conserva la más reciente)"
	@echo "make local-env      - instala el entorno local único (Fase 0 + ProtoMotions/MuJoCo)"
	@echo "make soma-mujoco-eval - evalúa el tracker Anatomical SOMA en MuJoCo, en el Mac"
	@echo "make checklist        - mide cada clip 5 veces en MuJoCo y actualiza docs/checklist_habilidades.md"
	@echo "make preflight        - revisión previa (\$$0) obligatoria antes de una corrida de GPU con cambios"

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

# PACKER_FLAGS=-on-error=abort deja viva la instancia si falla, para depurar por SSM.
# ¡Cuesta mientras siga encendida! Terminarla al acabar (make ami-kill-build).
PACKER_FLAGS ?=

ami: check-account ami-validate
	@command -v session-manager-plugin >/dev/null || { echo "Falta session-manager-plugin: brew install --cask session-manager-plugin"; exit 1; }
	cd infra/packer && packer build -timestamp-ui $(PACKER_FLAGS) .

ami-kill-build: check-account
	@ids=$$(aws ec2 describe-instances --filters Name=tag:Name,Values=humanoid-packer-build Name=instance-state-name,Values=pending,running,stopping,stopped --query 'Reservations[].Instances[].InstanceId' --output text); \
	if [ -n "$$ids" ]; then aws ec2 terminate-instances --instance-ids $$ids --query 'TerminatingInstances[].InstanceId' --output text; else echo "No hay instancias de build vivas."; fi

ami-cleanup: check-account
	./infra/packer/scripts/cleanup-old-amis.sh 1

local-env:
	cd phase0_basics && UV_HTTP_TIMEOUT=60 UV_HTTP_RETRIES=5 uv sync --python 3.12 --group protomotions

soma-mujoco-eval:
	./scripts/soma-mujoco-eval.sh

# Medición completa (~20 min en el Mac) + checklist. CHECKPOINT=... para medir un tracker propio (Fase 3b).
CHECKLIST_LABEL ?= Tracker NVIDIA preentrenado, sin ajuste
checklist:
	REPEATS=5 WORKERS=10 phase0_basics/.venv/bin/python retarget/eval_repeat.py repeat_latest
	phase0_basics/.venv/bin/python retarget/update_checklist.py data/cmu_motions/repeat_latest.json "$(CHECKLIST_LABEL)"

preflight:
	./scripts/preflight.sh
