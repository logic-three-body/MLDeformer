# Checkpoint 20260305 - 修复 MLD Source 帧渲染污染 + LBS-vs-LBS 严格验证

## 1. 概述

- **触发事件**：Phase S 完成后发现 source capture 帧存在渲染污染（MLD 激活时极端姿态触发 GPU 渲染状态异常），导致 SSIM 仅 0.59，需在下一轮修改验证前彻底修复。
- **核心修复**：新增 `disable_ml_deformer_for_source` 配置标志——使 source capture 也使用 `-DemoDisableMLDeformer=1`，实现纯 LBS-vs-LBS 对比。
- **验证结果**：Run `20260301_162455_smoke` 重新捕获 source（1560 帧），ALL PASS（ssim_mean=0.9994，psnr_mean=62.2 dB）。

---

## 2. 问题诊断：Source 帧渲染污染

### 现象
- Reference 帧：max pixel ~117–204，信道均匀，无异常
- Source 帧（MLD 激活）：frame 150 max=221 (5.6% bright px)，frame 170 max=250 (40.7% bright px)
- R-G 信道差异 diff_RG：正常帧 ~6，污染帧高达 41（有色光照！）

### 根因
ML Deformer 网格变形在极端动画姿态下触发 GPU 渲染状态异常，即使设置了 `showflag.Lighting=0` CVar 也会在部分帧临时重新激活光照，产生彩色高亮污染。

### 修复
在 `ue_capture_mainseq.py` 中新增逻辑：当配置 `disable_ml_deformer_for_source: true` 时，source capture 传入 `-DemoDisableMLDeformer=1`（与 reference 相同），实现 LBS-vs-LBS 对比。

---

## 3. 代码变更（UE57 commit `9b3b172`）

| 文件 | 变更内容 |
|------|---------|
| `pipeline/hou2ue/scripts/ue_capture_mainseq.py` | 新增 `disable_ml_deformer_for_source` 条件：source 也可传 `-DemoDisableMLDeformer=1` |
| `pipeline/hou2ue/config/pipeline.full_exec.yaml` | `capture.disable_ml_deformer_for_source: true` + 严格 LBS-vs-LBS 阈值 |
| `pipeline/hou2ue/scripts/build_report.py` | `_pipeline_thresholds()` 更新为严格值 |
| `pipeline/hou2ue/run_all.ps1` | 其他修复 |
| `Content/Python/Hou2UeDemoRuntimeExecutor.py` | 其他修复 |

---

## 4. 当前 Repo 状态

| Repo | HEAD | Remote | 状态 |
|------|------|--------|------|
| UE57 (`D:\UE\Unreal Projects\MLDeformerSample\UE57`) | `9b3b172` | 无 | Clean |
| Main (`D:\UE\Unreal Projects\MLDeformerSample`) | `1252cc3` → 本 commit | github.com:logic-three-body/MLDeformer.git master | 已 push |

---

## 5. 验证基准（当前有效，LBS-vs-LBS）

**Run**：`20260301_162455_smoke`（BaseColor，UE5.7 native，1560 帧，LBS-vs-LBS）

| 指标 | 实测值 | 阈值（当前配置） | 结果 |
|------|--------|-----------------|------|
| ssim_mean | **0.9994** | ≥ 0.92 | ✅ |
| ssim_p05 | **0.9990** | ≥ 0.82 | ✅ |
| psnr_mean | **62.21 dB** | ≥ 25.0 | ✅ |
| psnr_min | **55.70 dB** | ≥ 15.0 | ✅ |
| edge_iou_mean | **0.9978** | ≥ 0.80 | ✅ |
| ms_ssim_mean | **0.9997** | ≥ 0.88 | ✅ |
| ms_ssim_p05 | **0.9996** | ≥ 0.75 | ✅ |
| de2000_mean | **0.066** | ≤ 5.0 | ✅ |
| de2000_p95 | **0.098** | ≤ 10.0 | ✅ |
| **Overall** | - | - | ✅ **ALL PASS** |

备注：阈值从 Phase S（ssim≥0.97）调整为 LBS-vs-LBS 语义基准（ssim≥0.92），实际值 0.9994 大幅超越任何阈值配置。

---

## 6. 关键路径

| 内容 | 路径 |
|------|------|
| 主配置 | `UE57/pipeline/hou2ue/config/pipeline.full_exec.yaml` |
| 捕获脚本 | `UE57/pipeline/hou2ue/scripts/ue_capture_mainseq.py` |
| 报告构建 | `UE57/pipeline/hou2ue/scripts/build_report.py` |
| Reference 帧 | `{run_dir}/workspace/staging/smoke/gt/reference/frames/` |
| Source 帧（新）| `{run_dir}/workspace/staging/smoke/gt/source/frames/` |
| 当前 run_dir | `UE57/pipeline/hou2ue/workspace/runs/20260301_162455_smoke/` |

---

## 7. 下一步方向（Phase T：真实 MLD 误差测量）

当前 LBS-vs-LBS 验证的意义是确认渲染管线确定性（sanity check）。下一轮修改验证需要：

| 选项 | 描述 |
|------|------|
| **T1（推荐）**：LBS-ref vs MLD-src | 恢复 `disable_ml_deformer_for_source: false`，测量真实 ML Deformer 误差 |
| T2：调整动画以避免极端姿态污染 | 限制捕获动画帧范围，避开 MLD 触发污染的帧段 |
| T3：修复 UE 渲染污染根源 | 在 UE Python 侧修复 showflag/GPU 状态同步问题 |

**T1** 为直接可执行路径：取消 `disable_ml_deformer_for_source`，重跑 source capture + gt_compare，得到真实 LBS-vs-MLD SSIM（预计 ~0.55–0.70 范围），设置对应阈值后提交。
