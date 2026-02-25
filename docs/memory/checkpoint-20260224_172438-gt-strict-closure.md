# Checkpoint 20260224_172438 - GT Strict Closure Handoff

## 1. 目标（必须保持不变）
- 恢复并强制执行 strict GT 门禁：
  - `ssim_mean >= 0.995`
  - `ssim_p05 >= 0.985`
  - `psnr_mean >= 35`
  - `psnr_min >= 30`
  - `edge_iou_mean >= 0.97`
- 训练后（不是仅 baseline_sync 后）仍需通过 strict。
- 最终要求：`-Stage full` 成功，且 `gt_compare_report.json` 在 strict 下 `status=success`。

## 2. 当前结论（给零上下文接手者）
- GT 定义已确认正确：`Refference/MLDeformerSample.uproject` 的 `/Game/Main` + `Main_Sequence` 全序列。
- `20260223_233000_full` 这次 run：reference/source 均 1560 帧，说明抓取链路基本正确。
- 但当前 `pipeline.full_exec.yaml` 的阈值被放宽，导致“看似成功”。
- 关键问题不是“抓错 GT”，而是“训练后结果偏离 Reference 基线”。
- 偏差集中在角色躯干局部（胸背区域），典型帧段在 `~585-595`、`600-651`、`715-718`。

## 3. 关键证据路径
- 运行目录：`pipeline/hou2ue/workspace/runs/20260223_233000_full`
- GT 对比报告：`pipeline/hou2ue/workspace/runs/20260223_233000_full/reports/gt_compare_report.json`
- 推理报告：`pipeline/hou2ue/workspace/runs/20260223_233000_full/reports/infer_report.json`
- GT 帧：
  - `pipeline/hou2ue/workspace/runs/20260223_233000_full/workspace/staging/full/gt/reference/frames`
  - `pipeline/hou2ue/workspace/runs/20260223_233000_full/workspace/staging/full/gt/source/frames`
- 热力图：`pipeline/hou2ue/workspace/runs/20260223_233000_full/workspace/staging/full/gt/compare/heatmaps`

## 4. 当前仓库状态（接手前先看）
- `git status --short` 当前仅见：
  - `?? Content/Characters/Emil/Animation/Test/`
- 注意：此前存在较多流程改动历史，请先重新做一次 `git status` + 必要 diff 确认，再开始新改动。

## 5. 已实现到位的部分
- `run_all.ps1` 已含阶段：`baseline_sync/preflight/houdini/convert/ue_import/ue_setup/train/infer/gt_reference_capture/gt_source_capture/gt_compare/report`。
- `gt_compare` 已实现基础指标：SSIM/PSNR/Edge IoU + worst frames + heatmap。
- `baseline_sync`、`main sequence capture`、`infer demo` 主链路已存在。

## 6. 未完成/缺口（本次应优先补齐）
1. strict 门禁未彻底恢复
- `pipeline/hou2ue/config/pipeline.full_exec.yaml` 仍是放宽阈值（`0.98/0.95/35/29/0.969`）。
- 需要与 `pipeline.yaml`、`pipeline.strict_pdg_only.yaml` 统一 strict，并在汇总阶段防“静默放宽”。

2. 缺少 strict 防回退机制
- `pipeline/hou2ue/scripts/build_report.py` 尚未校验“阈值是否 strict 且是否允许 debug 放宽”。

3. 缺少 Deformer setup dump 能力（C++桥接未完成）
- 目前只有：`TrainDeformerAsset`、`SetupDeformerAsset`。
- 尚无：
  - `FMldDumpRequest`
  - `FMldDumpResult`
  - `UMLDTrainAutomationLibrary::DumpDeformerSetup(...)`
- 相关文件：
  - `Source/MLDeformerSampleEditorTools/Public/MLDTrainTypes.h`
  - `Source/MLDeformerSampleEditorTools/Public/MLDTrainAutomationLibrary.h`
  - `Source/MLDeformerSampleEditorTools/Private/MLDTrainAutomationLibrary.cpp`

4. strict_clone 流程未落地
- `ue_setup_assets.py` 目前是 `reference_baseline.deformer_assets_override` 的合并覆盖，不是“Reference dump 全量克隆 + 字段 diff”。
- 缺少：`reference_setup_dump.json`、`setup_diff_report.json`。

5. determinism 治理未落地
- 配置中未见 `ue.training.determinism`。
- 脚本中未产生 `train_determinism_report.json`，train 阶段没有统一 seed/确定性记录。

6. compare 报告增强未落地
- `compare_groundtruth.py` 还没有：
  - `strict_profile_name`
  - `strict_thresholds_hash`
  - 按 100 帧窗口统计
  - body ROI 指标（角色中心区域）

## 7. 建议接手执行顺序（可直接照做）
1. 恢复 strict 阈值与门禁
- 修改：
  - `pipeline/hou2ue/config/pipeline.full_exec.yaml`
  - `pipeline/hou2ue/config/pipeline.yaml`
  - `pipeline/hou2ue/config/pipeline.strict_pdg_only.yaml`
  - `pipeline/hou2ue/scripts/build_report.py`
- 目标：默认必须 strict，除非显式 `debug_mode=true`。

2. 补 C++ dump 接口 + Python 调用链
- 修改：
  - `Source/MLDeformerSampleEditorTools/Public/MLDTrainTypes.h`
  - `Source/MLDeformerSampleEditorTools/Public/MLDTrainAutomationLibrary.h`
  - `Source/MLDeformerSampleEditorTools/Private/MLDTrainAutomationLibrary.cpp`
- 新增（建议）：
  - `pipeline/hou2ue/scripts/dump_reference_setup.py`
- 产物：`reports/reference_setup_dump.json`。

3. 把 ue_setup 改为 strict_clone 优先
- 修改：`pipeline/hou2ue/scripts/ue_setup_assets.py`
- 逻辑：优先使用 Reference dump 全量字段写入，再生成字段级 diff。
- 产物：`reports/setup_diff_report.json`。

4. 加 determinism
- 修改：
  - `pipeline/hou2ue/config/*.yaml`（新增 `ue.training.determinism`）
  - `pipeline/hou2ue/run_all.ps1`
  - `pipeline/hou2ue/scripts/ue_train.py`
- 产物：`reports/train_determinism_report.json`（含 seed、环境标志、训练时序）。

5. 增强 gt_compare
- 修改：`pipeline/hou2ue/scripts/compare_groundtruth.py`
- 加入 strict hash、窗口统计、body ROI 指标。
- 结果写入：`reports/gt_compare_report.json`。

6. 做 A/B 证据闭环 + 3次稳定性复跑
- 组1（不重训）：`baseline_sync -> gt_reference_capture -> gt_source_capture -> gt_compare`
- 组2（重训）：`baseline_sync -> ue_setup -> train -> infer -> gt_reference_capture -> gt_source_capture -> gt_compare`
- 要求：同一 strict 配置下，组2 连续 3 次均 pass。

## 8. 可直接执行的命令模板
- 全流程：
```powershell
pwsh pipeline/hou2ue/run_all.ps1 -Stage full -Profile full -Config pipeline/hou2ue/config/pipeline.full_exec.yaml
```
- 只做 GT 采集与对比（同一 RunDir）：
```powershell
pwsh pipeline/hou2ue/run_all.ps1 -Stage gt_reference_capture -Profile full -Config pipeline/hou2ue/config/pipeline.full_exec.yaml -RunDir <run_dir>
pwsh pipeline/hou2ue/run_all.ps1 -Stage gt_source_capture -Profile full -Config pipeline/hou2ue/config/pipeline.full_exec.yaml -RunDir <run_dir>
pwsh pipeline/hou2ue/run_all.ps1 -Stage gt_compare -Profile full -Config pipeline/hou2ue/config/pipeline.full_exec.yaml -RunDir <run_dir>
```
- 仅重训验证（同一 RunDir 串行）：
```powershell
pwsh pipeline/hou2ue/run_all.ps1 -Stage ue_setup -Profile full -Config pipeline/hou2ue/config/pipeline.full_exec.yaml -RunDir <run_dir>
pwsh pipeline/hou2ue/run_all.ps1 -Stage train -Profile full -Config pipeline/hou2ue/config/pipeline.full_exec.yaml -RunDir <run_dir>
pwsh pipeline/hou2ue/run_all.ps1 -Stage infer -Profile full -Config pipeline/hou2ue/config/pipeline.full_exec.yaml -RunDir <run_dir>
```

## 9. 约束与注意事项
- GroundTruth 唯一来源：`Refference` 工程 `Main.umap + Main_Sequence`。
- 目标是“训练后 strict 通过”，不是“放宽阈值后看起来可用”。
- 同一 `RunDir` 阶段必须串行，避免 `run_info.json` 竞争。
- 大文件与 `Refference` 相关内容按本地基线使用，不进入远端推送策略。

## 10. 接手即做的第一步（建议）
- 先恢复 `pipeline.full_exec.yaml` 到 strict，并给 `build_report.py` 加 strict 防回退检查；
- 然后立即跑一组 `gt_compare` 验证“strict 当前确实 fail”，作为后续修复基线。
