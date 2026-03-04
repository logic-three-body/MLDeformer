# Checkpoint 20260304 - Phase S 完成 + 待解决问题

## 1. 概述

- **触发事件**：Phase S（阈值收紧）全部完成，UE5.7 原生训练管线仍有 D3D12 TDR 崩溃待解决。
- **核心成果**：
  1. Phase R (BaseColor 渲染模式) R1–R7 全部完成
  2. Phase S S1（阈值收紧）+ S2/S3（验证）全部通过
  3. Run `20260301_162455_smoke`：1560 帧 BaseColor，ALL PASS（strict 阈值）
  4. Heatmap 自动归一化修复已提交
  5. MS-SSIM + CIEDE2000 (ΔE2000) 新指标集成

---

## 2. 当前 Repo 状态

| Repo | HEAD | Remote | 状态 |
|------|------|--------|------|
| UE57 (`D:\UE\Unreal Projects\MLDeformerSample\UE57`) | `c3b99b3` | 无 | Clean |
| Main (`D:\UE\Unreal Projects\MLDeformerSample`) | `0f17e32` | github.com:logic-three-body/MLDeformer.git master | Clean，已 push |

---

## 3. 验证基准（当前有效阈值）

**Run**：`20260301_162455_smoke`（BaseColor，UE5.7 native，1560 帧）

| 指标 | 实测值 | 阈值 | 结果 |
|------|--------|------|------|
| ssim_mean | 0.9995 | ≥ 0.97 | ✅ |
| ssim_p05 | 0.9990 | ≥ 0.92 | ✅ |
| psnr_mean | 62.1 dB | ≥ 40.0 | ✅ |
| psnr_min | 55.7 dB | ≥ 35.0 | ✅ |
| edge_iou_mean | 0.9990 | ≥ 0.92 | ✅ |
| ms_ssim_mean | 0.9998 | ≥ 0.995 | ✅ |
| ms_ssim_p05 | 0.9996 | ≥ 0.97 | ✅ |
| de2000_mean | 0.075 | ≤ 1.0 | ✅ |
| de2000_p95 | 0.134 | ≤ 2.5 | ✅ |

Config 位置：`UE57/pipeline/hou2ue/config/pipeline.full_exec.yaml` §compare.thresholds

---

## 4. 关键路径

| 内容 | 路径 |
|------|------|
| 主配置 | `UE57/pipeline/hou2ue/config/pipeline.full_exec.yaml` |
| 图片输出根目录 | `{run_dir}/workspace/staging/smoke/gt/` |
| Reference 帧 | `{run_dir}/workspace/staging/smoke/gt/reference/frames/` |
| Source 帧 | `{run_dir}/workspace/staging/smoke/gt/source/frames/` |
| Heatmap | `{run_dir}/workspace/staging/smoke/gt/compare/heatmaps/` |
| 当前 run_dir | `UE57/pipeline/hou2ue/workspace/runs/20260301_162455_smoke/` |
| Checklist | `UE57/docs/07_ue57_compat/README_UE57_Migration_Checklist_CN.md` |
| Phase S 计划 | `docs/plan/phase_S_plan.md` |

`run_dir` 根可通过 `run_all.ps1 -OutRoot <路径>` 修改（默认第 10 行）。

---

## 5. 问题状态（2026-03-04 更新）

### ✅ P1：UE5.7 训练 D3D12 TDR 崩溃 → **已解决**

**诊断结论**：TDR=300s（`0x12c`）+ 驱动 576.57（≥ 572.16）+ 双 RTX 4090 + train 阶段 `-nullrhi` 组合修复。
Run `20260301_162455_smoke` 实测：NMM flesh 训练 281.99s，status=success。无需进一步操作。

---

### ✅ P3：完整端到端 smoke 重测 → **已完成**

**Run `20260301_162455_smoke`，12/12 阶段全部 success，严格阈值 ALL PASS。**

`pipeline_report_latest.json` status=success, errors=0（2026-03-04 生成）

**附加修复**：`build_report.py` 阈值检查改为「至少同等严格」语义（commit `0896b3a` UE57），
允许 Phase S 超严格阈值通过 pipeline-source 检查。

---

### 🟡 P2：Phase S2 双轨对比（可选，待决策）

- **Option A（当前）**：仅 BaseColor 自比较 ✅，无需额外工作
- **Option B/C**：见 `docs/plan/phase_S_plan.md §S2`
- **决策条件**：对外演示 UE5.5→UE5.7 对齐时实施 B 或 C，否则 A 足够。

---

## 6. 已完成里程碑

| 里程碑 | 提交 | 日期 |
|--------|------|------|
| BaseColor ShowFlag 实现 (R1-R5) | `98e26ba` (UE57) | 2026-03-01 |
| Heatmap 自动归一化 | `f995219` (UE57) | 2026-03-01 |
| MS-SSIM + ΔE2000 指标 | UE57 commit | 2026-03-03 |
| Phase S 阈值收紧 + R7 完成 | `c3b99b3` (UE57) | 2026-03-04 |
| Phase S 计划完成 (main) | `0f17e32` (main) | 2026-03-04 |
| build_report 阈值检查修复 | `0896b3a` (UE57) | 2026-03-04 |
| Run 20260301_162455_smoke 全链路 12/12 success | pipeline_report_latest.json | 2026-03-04 |
