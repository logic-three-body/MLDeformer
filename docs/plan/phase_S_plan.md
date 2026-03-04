# 阶段 S 修改计划：阈值收紧 + 双轨对比

> **背景**：Phase R（BaseColor 渲染模式）已于 `20260301_162455_smoke` 全面验证通过
> （SSIM=0.9995, PSNR=62.1 dB, 1560 帧 ALL PASS）。
> 本计划为 Phase R 完成后的下一步工作。

---

## 已确认状态

| 项目 | 状态 |
|------|------|
| BaseColor 渲染模式（R1–R5） | ✅ 已实现并提交 |
| Run `20260301_162455_smoke`：GT 对比 SSIM=0.9995 | ✅ |
| Heatmap 自动归一化修复 | ✅ 已提交 `f995219` |
| 相机机位验证（未发生变化） | ✅ 调查完成，见 checklist §R |
| UE57 docs 更新 | ✅ 已提交 `38570cd` |
| **S1：阈值收紧 + debug_mode 移除** | ✅ 已提交 UE57 `c3b99b3`（2026-03-04）|
| **S2（S3）：gt_compare 验证新阈值 ALL PASS** | ✅ Run `20260301_162455_smoke` ALL PASS |

---

## S1：收紧 SSIM 阈值（直接可执行）

**目标**：BaseColor 模式下消除了 Lumen 底线噪声，SSIM 均值 0.9995 远超旧阈值 0.80。
将阈值收紧至反映 BaseColor 精度预期的水平，并移除 `debug_mode` 标志。

**改动位置**：`pipeline/hou2ue/config/pipeline.full_exec.yaml`（和/或 `pipeline.yaml`）

| 参数 | 旧值 | 新值 | 说明 |
|------|------|------|------|
| `ssim_mean_min` | 0.80 | 0.97 | BaseColor 自比较基准 |
| `ssim_p05_min` | 0.60 | 0.92 | 最差 5% 帧 |
| `psnr_mean_min` | 22.0 | 40.0 | dB |
| `debug_mode` | `true` | `false` | 移除跳帧加速 |

**验证方法**：重跑 `gt_compare` 步骤（无需重新渲染，使用已有帧）确认 ALL PASS。

**提交**：`fix: tighten BaseColor SSIM/PSNR thresholds, remove debug_mode`

---

## S2：建立双轨对比（可选，待讨论）

**背景**：旧 run `20260226_200951_smoke` 量的是跨引擎兼容性（UE5.5 Lit vs UE5.7 Lit，
SSIM=0.845），新 run 量的是 ML Deformer 纯精度（UE5.7 BC ref vs UE5.7 BC src，
SSIM=0.9995）。两者衡量不同维度，有时需要同时追踪。

**方案 A（推荐）：维持现状，仅 BaseColor 自比较**
- 优点：SSIM 接近 1.0，噪声极低，精确反映 deformer 误差
- 优点：无跨引擎/跨渲染模式混淆
- 缺点：无法直接量化"UE5.7 输出与 UE5.5 外观差异"

**方案 B：恢复 UE5.5 静态旁路作为第二轨道（cross-engine track）**
- 在 pipeline 中新增可选步骤 `gt_cross_engine_compare`
- `static_reference_frames_dir` 指向 `20260226_170226_smoke` 的 UE5.5 Lit 帧
- `render_mode: lit`（source 也用 Lit 渲染，与 UE5.5 可比）
- 两轨报告分开：`gt_compare_basecolor_report.json` / `gt_compare_crossengine_report.json`
- 复杂度高，仅在需要发布/演示 UE5.5 对齐时才实施

**方案 C：渲染 UE5.7 Lit reference 作为 Lit 对比基准**
- 在 UE5.7 下重新捕获 Lit 渲染 reference（无 ML Deformer）
- 与 UE5.7 Lit source（有 ML Deformer）比较
- 优点：同引擎 Lit 对比，SSIM 预计 ~0.99+，无 Lumen 冷启动问题（warmup 已修复）
- 缺点：又一次完整捕获（~1560 帧 × Lit 分辨率）

**当前建议**：先执行 S1（收紧阈值），S2 等待用户确认方向后再实施。

---

## S3：端到端 smoke 重测（S1 完成后）

1. 清理 staging 目录
2. 运行完整 pipeline（`full_exec`）：训练 → reference capture → source capture → gt_compare
3. 确认新阈值下 ALL PASS
4. 结果归档至 `runs/YYYYMMDD_HHMMSS_smoke/`

---

## 优先级顺序

```
S1（收紧阈值）→ S3（重测验证）→ 视需要决定 S2 方向
```

---

## 相关文件

- `pipeline/hou2ue/config/pipeline.full_exec.yaml`：阈值参数
- `pipeline/hou2ue/config/pipeline.yaml`：默认值
- `pipeline/hou2ue/scripts/compare_groundtruth.py`：对比逻辑
- `UE57/docs/07_ue57_compat/README_UE57_Migration_Checklist_CN.md`：R 阶段 checklist
