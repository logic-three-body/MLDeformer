---
name: prototype-data-acquisition
description: Acquire public/gated assets with state tracking, then build dataset manifest and QC outputs for the MLDeformer prototype.
---

# Prototype Data Acquisition Skill

## trigger
- 需要初始化或刷新原型数据集。
- 新增资产来源后需要统一状态追踪。
- 训练前需要确保数据清单与QC结果存在。

## prerequisites
- `prototype/config/assets.manifest.yaml` 已定义资产条目。
- Windows 数据根目录可写（默认 `D:/MLDPrototypeData`）。
- Python 可用并安装 `PyYAML`。

## steps
1. 执行公开资产下载：`python prototype/scripts/fetch_public_assets.py --data-root D:/MLDPrototypeData`。
2. 执行受限资产流程：`python prototype/scripts/fetch_gated_assets.py --data-root D:/MLDPrototypeData`。
3. 生成数据清单：`python prototype/scripts/build_dataset.py --data-root D:/MLDPrototypeData`。
4. 检查 `prototype/state/assets_status.json`，确认受限源失败以 `manual_pending` 记录而非中断。

## outputs
- `prototype/state/assets_status.json`
- `D:/MLDPrototypeData/processed/dataset_manifest.jsonl`
- `D:/MLDPrototypeData/processed/dataset_summary.json`

## failure_modes
- URL 失效导致 `failed`。
- 受限资源无凭据导致 `manual_pending`。
- 数据目录权限不足导致写入失败。

## verification
- 状态文件存在且包含每个 `asset_id`。
- `dataset_manifest.jsonl` 每行含 `sample_id/split/modality/qc_status`。
- 至少一个公开资源状态为 `ready`。
