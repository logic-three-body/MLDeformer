---
name: prototype-wsl-train-orchestrator
description: Orchestrate NMM/NNM/Groom smoke training in WSL and generate standardized train reports.
---

# Prototype WSL Train Orchestrator Skill

## trigger
- 需要在 WSL 验证训练链路可执行。
- 需要快速对比 NMM/NNM/Groom 三方法训练产物。
- 推理阶段前缺少训练报告。

## prerequisites
- WSL 可用且可访问仓库路径。
- `nvidia-smi` 可正常输出 GPU 信息。
- 数据根目录已准备（默认 `/root/Project/MLDPrototypeData`）。

## steps
1. 初始化 WSL 环境：`bash prototype/scripts/bootstrap_wsl.sh mimickit /root/Project/MLDPrototypeData`。
2. 运行 smoke：`bash prototype/scripts/train_wsl.sh smoke --data-root /root/Project/MLDPrototypeData --gpus 0,1`。
3. 运行单方法回归（可选）：`bash prototype/scripts/train_wsl.sh nmm --data-root ...`。
4. 检查 `artifacts/train/*/train_report.json` 与索引文件。

## outputs
- `/root/Project/MLDPrototypeData/artifacts/train/<method>/train_report.json`
- `/root/Project/MLDPrototypeData/artifacts/train/train_reports_index.json`
- `/root/Project/MLDPrototypeData/artifacts/train/<method>/model_stub.bin`

## failure_modes
- `nvidia-smi` 不可用导致训练前失败。
- Python 环境缺依赖导致脚本异常。
- 数据根目录未创建导致产物写入失败。

## verification
- 三个方法均生成 `train_report.json`。
- `status` 字段为 `smoke_stub_success`。
- 报告含 `method/config_hash/gpu/wall_time/train_loss/val_loss` 字段。
