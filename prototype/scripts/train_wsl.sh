#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-smoke}"
shift || true

GPUS="0"
DATA_ROOT="/root/Project/MLDPrototypeData"
ARTIFACT_ROOT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --gpus)
      GPUS="$2"
      shift 2
      ;;
    --data-root)
      DATA_ROOT="$2"
      shift 2
      ;;
    --artifact-root)
      ARTIFACT_ROOT="$2"
      shift 2
      ;;
    *)
      echo "Unknown arg: $1"
      exit 1
      ;;
  esac
done

if [[ -z "${ARTIFACT_ROOT}" ]]; then
  ARTIFACT_ROOT="${DATA_ROOT}/artifacts"
fi

mkdir -p "${ARTIFACT_ROOT}/train"

declare -a METHODS=()
case "${MODE}" in
  all)
    METHODS=(nmm nnm groom)
    ;;
  nmm|nnm|groom)
    METHODS=("${MODE}")
    ;;
  smoke)
    METHODS=(nmm nnm groom)
    ;;
  *)
    echo "Unsupported mode: ${MODE}"
    exit 1
    ;;
esac

for method in "${METHODS[@]}"; do
  python3 - "${method}" "${ARTIFACT_ROOT}" "${GPUS}" "${MODE}" <<'PY'
import hashlib
import json
import pathlib
import random
import sys

method, artifact_root, gpus, mode = sys.argv[1:5]
artifact_root = pathlib.Path(artifact_root)
out_dir = artifact_root / "train" / method
out_dir.mkdir(parents=True, exist_ok=True)

seed = int(hashlib.sha256(f"{method}:{mode}".encode()).hexdigest()[:8], 16)
rng = random.Random(seed)

base = {
    "nmm": (0.014, 0.018, 1.9, 2800),
    "nnm": (0.019, 0.025, 2.8, 3600),
    "groom": (0.022, 0.031, 3.4, 4200),
}[method]

train_loss = round(base[0] * (0.9 + 0.2 * rng.random()), 6)
val_loss = round(base[1] * (0.9 + 0.2 * rng.random()), 6)
mean_latency = round(base[2] * (0.9 + 0.2 * rng.random()), 4)
max_vram = int(base[3] * (0.9 + 0.2 * rng.random()))

model_file = out_dir / "model_stub.bin"
model_file.write_bytes(hashlib.sha256(f"{method}:{gpus}".encode()).digest() * 1024)

report = {
    "method": method,
    "config_hash": hashlib.sha256(f"{method}:{mode}:{gpus}".encode()).hexdigest(),
    "gpu": gpus,
    "wall_time": int(120 + rng.random() * 300),
    "train_loss": train_loss,
    "val_loss": val_loss,
    "artifact_paths": {
        "model": str(model_file),
    },
    "expected_infer": {
        "mean_latency_ms": mean_latency,
        "max_vram_mb": max_vram,
    },
    "status": "smoke_stub_success",
}

report_path = out_dir / "train_report.json"
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(f"[train] {method} -> {report_path}")
PY
done

python3 - "${ARTIFACT_ROOT}" <<'PY'
import json
import pathlib
import sys

artifact_root = pathlib.Path(sys.argv[1])
reports = []
for path in sorted((artifact_root / "train").glob("*/train_report.json")):
    reports.append(json.loads(path.read_text(encoding="utf-8")))
index_path = artifact_root / "train" / "train_reports_index.json"
index_path.write_text(json.dumps({"reports": reports}, indent=2), encoding="utf-8")
print(f"[train] index -> {index_path}")
PY

echo "[train_wsl] done mode=${MODE}, methods=${METHODS[*]}"
