#!/usr/bin/env bash
# Entorno de medición en un runner Ubuntu de GitHub Actions (CPU, sin GPU): ProtoMotions @13de0ccc con el tracker
# de NVIDIA (Git LFS, solo los archivos que se usan) y las mismas versiones que el entorno local (phase0_basics/uv.lock),
# pero con torch de CPU (sin los ~3 GB de CUDA). Render offscreen con EGL de Mesa.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$REPO"
PM_COMMIT=13de0ccc

sudo apt-get update -qq
sudo apt-get install -y -qq ffmpeg libegl1 libgl1 libegl-mesa0 libgles2 git-lfs fonts-dejavu-core >/dev/null

if [[ ! -d third_party/ProtoMotions/.git ]]; then
  GIT_LFS_SKIP_SMUDGE=1 git clone -q --filter=blob:none https://github.com/NVlabs/ProtoMotions.git third_party/ProtoMotions
fi
( cd third_party/ProtoMotions
  git -c advice.detachedHead=false checkout -q "$PM_COMMIT"
  git lfs install --local >/dev/null
  git lfs pull --include "data/pretrained_models/motion_tracker/anatomic_soma_bones_fsq/inference_last.ckpt,data/motion_for_trackers/anatomic_soma_bones_seed_mini.pt" )

curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null
export PATH="$HOME/.local/bin:$PATH"
uv venv -q --python 3.12 .venv-ci
torch_ver=$(cd phase0_basics && uv export --frozen --group protomotions --no-hashes | sed -n 's/^torch==\([0-9.]*\).*/\1/p' | head -1)
VIRTUAL_ENV=.venv-ci uv pip install -q "torch==$torch_ver" --index-url https://download.pytorch.org/whl/cpu
( cd phase0_basics && uv export --frozen --group protomotions --no-hashes --no-emit-project ) \
  | grep -vE '^(torch|torchvision|torchaudio|triton|cuda-[a-z-]+|nvidia-[a-z0-9-]+)==' | grep -vE '^\s*#' > /tmp/req-ci.txt
( cd phase0_basics && VIRTUAL_ENV=../.venv-ci uv pip install -q --no-deps -r /tmp/req-ci.txt )  # lista completa del lock: no re-resuelve (no trae torch CUDA)
.venv-ci/bin/python -c "import torch, mujoco, protomotions; print('torch', torch.__version__, '| mujoco', mujoco.__version__)"
