#!/usr/bin/env bash
# Provisiona la AMI de entrenamiento. Corre como root en la instancia de build (sin GPU).
#
# Importante: este script NO acepta la EULA de Isaac Sim. La aceptación la hace Brandon,
# guardando el parámetro SSM /humanoid/isaacsim/eula_accepted = "yes"; el script de arranque
# (/opt/humanoid/env.sh) solo exporta OMNI_KIT_ACCEPT_EULA si ese parámetro existe.
set -euo pipefail

: "${ISAACLAB_COMMIT:?falta ISAACLAB_COMMIT}"
: "${PROTOMOTIONS_COMMIT:?falta PROTOMOTIONS_COMMIT}"

ROOT=/opt/humanoid
VENV="$ROOT/venv"
export DEBIAN_FRONTEND=noninteractive

log() { echo "==> $*"; }

log "Paquetes del sistema"
apt-get update -y
apt-get install -y --no-install-recommends \
  git git-lfs ffmpeg jq unzip \
  libgl1 libglu1-mesa libegl1 libxrandr2 libxinerama1 libxcursor1 libxi6 libxt6
git lfs install --system

log "AWS CLI"
if ! command -v aws >/dev/null 2>&1; then
  curl -sSfL -o /tmp/awscliv2.zip https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip
  unzip -q /tmp/awscliv2.zip -d /tmp && /tmp/aws/install && rm -rf /tmp/aws /tmp/awscliv2.zip
fi

log "uv"
curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin INSTALLER_NO_MODIFY_PATH=1 sh

mkdir -p "$ROOT"
chown ubuntu:ubuntu "$ROOT"

# Todo lo de Python se instala como ubuntu, no como root.
sudo -u ubuntu -H env ROOT="$ROOT" VENV="$VENV" \
  ISAACLAB_COMMIT="$ISAACLAB_COMMIT" PROTOMOTIONS_COMMIT="$PROTOMOTIONS_COMMIT" \
  bash -euo pipefail <<'USER_EOF'
log() { echo "==> $*"; }
cd "$ROOT"

log "Isaac Lab @ ${ISAACLAB_COMMIT}"
git clone --filter=blob:none https://github.com/isaac-sim/IsaacLab.git
git -C IsaacLab checkout --quiet "$ISAACLAB_COMMIT"

log "ProtoMotions @ ${PROTOMOTIONS_COMMIT} (sin bajar todos los archivos LFS)"
GIT_LFS_SKIP_SMUDGE=1 git clone --filter=blob:none https://github.com/NVlabs/ProtoMotions.git
git -C ProtoMotions checkout --quiet "$PROTOMOTIONS_COMMIT"

log "Checkpoints y clips de ejemplo: solo Anatomical SOMA y SOMA23 (plan B)"
git -C ProtoMotions lfs pull --include="\
data/pretrained_models/motion_tracker/anatomic_soma_bones_fsq/**,\
data/pretrained_models/gpc_prior/anatomic_soma_bones/**,\
data/pretrained_models/motion_tracker/soma_bones_fsq/**,\
data/pretrained_models/gpc_prior/soma_bones/**,\
data/motion_for_trackers/*soma*"

log "Entorno Python 3.12"
uv venv --python 3.12 "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
export UV_HTTP_TIMEOUT=600

log "Isaac Lab + Isaac Sim (pip)"
(cd IsaacLab && uv pip install -e ".[isaacsim]" --extra-index-url https://pypi.nvidia.com)

log "ProtoMotions (backend Isaac Lab)"
uv pip install -e "$ROOT/ProtoMotions[isaaclab]" --extra-index-url https://pypi.nvidia.com
uv pip install -r "$ROOT/ProtoMotions/requirements_isaaclab.txt" --extra-index-url https://pypi.nvidia.com

log "MuJoCo (compuerta de validación del runtime del juego)"
uv pip install "mujoco>=3"

log "Limpieza de caché"
uv cache clean
USER_EOF

log "Verificaciones (sin GPU)"
sudo -u ubuntu -H bash -euo pipefail <<'CHECK_EOF'
source /opt/humanoid/venv/bin/activate
python - <<'PY'
import importlib, sys
for mod in ("torch", "mujoco", "protomotions"):
    m = importlib.import_module(mod)
    print(f"OK {mod} {getattr(m, '__version__', '')}")
print("python", sys.version.split()[0])
PY
CHECK_EOF

# Un archivo LFS sin bajar es un "pointer" de ~130 bytes y rompe la carga de modelos.
bad=0
while IFS= read -r -d '' f; do
  if head -c 64 "$f" | grep -q "git-lfs.github.com/spec"; then
    echo "ERROR: archivo LFS sin descargar: $f"; bad=1
  fi
done < <(find "$ROOT/ProtoMotions/data/pretrained_models" -type f -print0)
[[ $bad -eq 0 ]] || exit 1
find "$ROOT/ProtoMotions/data/pretrained_models" -name '*.ckpt' -exec ls -lh {} \;

log "Script de entorno de ejecución"
cat > "$ROOT/env.sh" <<'ENV_EOF'
# Cargar con: source /opt/humanoid/env.sh
source /opt/humanoid/venv/bin/activate
export PROTOMOTIONS_ROOT=/opt/humanoid/ProtoMotions
export ISAACLAB_ROOT=/opt/humanoid/IsaacLab
# La EULA de Isaac Sim solo se da por aceptada si Brandon guardó el parámetro.
if [[ "$(aws ssm get-parameter --name /humanoid/isaacsim/eula_accepted --query Parameter.Value --output text 2>/dev/null)" == "yes" ]]; then
  export OMNI_KIT_ACCEPT_EULA=YES
else
  echo "AVISO: la EULA de Isaac Sim no está aceptada (/humanoid/isaacsim/eula_accepted). Isaac Lab no arrancará." >&2
fi
ENV_EOF
chmod 644 "$ROOT/env.sh"

log "Limpieza del sistema"
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/*
# Que cada instancia nueva genere sus propias llaves e identidad.
rm -f /etc/ssh/ssh_host_*
truncate -s 0 /etc/machine-id
du -sh "$ROOT"
log "Listo"
