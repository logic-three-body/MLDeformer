#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${1:-mimickit}"
DATA_ROOT="${2:-/root/Project/MLDPrototypeData}"
SKIP_PIP_INSTALL="${3:-0}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "[bootstrap_wsl] repo: ${REPO_ROOT}"
echo "[bootstrap_wsl] data_root: ${DATA_ROOT}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found"
  exit 1
fi

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "nvidia-smi not found, CUDA driver unavailable"
  exit 1
fi

nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

mkdir -p "${DATA_ROOT}/raw" "${DATA_ROOT}/processed" "${DATA_ROOT}/artifacts" "${DATA_ROOT}/downloads" "${DATA_ROOT}/logs"

if ! command -v conda >/dev/null 2>&1; then
  for conda_sh in \
    "$HOME/miniconda3/etc/profile.d/conda.sh" \
    "$HOME/anaconda3/etc/profile.d/conda.sh" \
    "/opt/conda/etc/profile.d/conda.sh"; do
    if [[ -f "${conda_sh}" ]]; then
      # shellcheck disable=SC1090
      source "${conda_sh}"
      break
    fi
  done
fi

if command -v conda >/dev/null 2>&1; then
  # shellcheck disable=SC1091
  source "$(conda info --base)/etc/profile.d/conda.sh"
  if conda env list | awk '{print $1}' | grep -qx "${ENV_NAME}"; then
    conda activate "${ENV_NAME}"
    echo "[bootstrap_wsl] activated conda env: ${ENV_NAME}"
  else
    echo "[bootstrap_wsl] conda env not found: ${ENV_NAME} (continue without activation)"
  fi
else
  echo "[bootstrap_wsl] conda not found (continue with system python)"
fi

python3 - <<'PY'
mods = ["yaml", "json", "hashlib"]
missing = []
for m in mods:
    try:
        __import__(m)
    except Exception:
        missing.append(m)
if missing:
    print("missing modules:", ", ".join(missing))
else:
    print("python module check passed")
PY

if [[ -f "${SCRIPT_DIR}/../requirements_wsl.txt" ]]; then
  if [[ "${SKIP_PIP_INSTALL}" == "1" ]]; then
    echo "[bootstrap_wsl] skip pip install (SKIP_PIP_INSTALL=1)"
  elif python3 -m pip --version >/dev/null 2>&1; then
    python3 -m pip install -r "${SCRIPT_DIR}/../requirements_wsl.txt"
  else
    echo "[bootstrap_wsl] python3 -m pip not available, skip requirements install"
  fi
fi

echo "[bootstrap_wsl] done"
