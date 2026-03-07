# Checkpoint: Phase U Complete — NMM 5kGreedyROM 训练失败，模型过大 (2026-03-07)

## 概要

Phase U 目标：用 `GC_upperBodyFlesh_5kGreedyROM`（8.46 GB，5000 poses，宽 pose 覆盖）
从零重新训练 NMM flesh upperBody，期望复现 Epic Refference 模型质量（ssim=0.9142）。

**两次完整训练均失败，指标几乎相同：**

| 尝试 | 情况 | ssim_mean | psnr_mean | 结果 |
|------|------|-----------|-----------|------|
| U v1（断点续训，iter 24700→25000） | GPU TDR 多次崩溃后恢复 | 0.6647 | 17.84 | ❌ |
| U v2（全新从 iter 1 开始）| GPU 稳定，loss 正常下降 | 0.6600 | 17.72 | ❌ |
| Refference NMM（Epic 原厂） | 未训练，直接使用 | 0.9142 | 30.63 | ✅ |

**指标几乎完全一致（ssim 差 <0.005），说明断点续训非根因。问题是系统性的。**

---

## 关键发现：模型尺寸差距 5.76×

| 资产 | 大小 | 修改时间 |
|------|------|---------|
| 我方训练后 `MLD_NMMl_flesh_upperBody.uasset` | **1680 MB** | 2026-03-07 15:40 |
| Epic Refference `MLD_NMMl_flesh_upperBody.uasset` | **292 MB** | 2026-02-01 |

我方训练出的模型体积是 Refference 的 **5.76 倍**。

NMM uasset 的体积主要由 **local morph targets（局部形态键数量 × 顶点数 × 3 float）**
决定，与训练迭代次数无关。体积差异说明：
- 我方模型生成了远多于 Refference 的 local morphs（可能由输入 GC 帧数自动推算）
- 参数自由度过多（过拟合/噪声拟合）→ 对 Main_Sequence 泛化性差 → 大量错误形变

---

## 训练过程（U v2，干净运行）

| 阶段 | 值 |
|------|-----|
| iter 1 loss | 0.2036 |
| iter 5000 loss | ~0.016 |
| iter 25000 loss | 0.0167 |
| lr（最终） | ~0.000000 |
| GPU 显存 | 6.65 GB |
| 训练数据缓存 | inputs.bin=10.4 GB，outputs.bin=6.4 GB |
| 总耗时 | ~2.5 小时 |
| `training_processor_api_present` | `false` |

Loss 正常下降，没有崩溃。但训练 loss 不能代表对 Main_Sequence 的泛化性。

---

## 完整闭环结果（U v2）

| 阶段 | 状态 | 关键值 |
|------|------|--------|
| train | ✅ success | 25000 iters, loss=0.0167, 模型 1680 MB |
| gt_source_capture | ✅ success | 1560 帧，-d3dadapter=1 |
| gt_compare | ❌ failed | ssim=0.660, psnr=17.72 |
| report | ✅ generated | `pipeline_report_20260307_082010.json` |

gt_compare 失败阈值列表（阈值均未达）：

| 指标 | 实际 | 阈值 |
|------|------|------|
| ssim_mean | 0.660 | ≥ 0.83 |
| psnr_mean | 17.72 dB | ≥ 22.0 dB |
| ms_ssim_mean | 0.564 | ≥ 0.80 |
| de2000_mean | 9.35 | ≤ 8.0 |
| edge_iou_mean | 0.541 | ≥ 0.82 |

---

## 根因假设

1. **NMM 局部形态键数量未限制**：pipeline 配置仅设 `num_iterations: 25000`，
   未设 `num_local_morphs` / `num_global_morphs`。5kGreedyROM（5000帧）作为
   输入时，UE NMM 训练器可能自动从 GC 数据推算出大量 PCA basis，导致模型膨胀。

2. **Refference 模型可能有受限的架构**：292 MB vs 1680 MB 说明 Epic 训练时
   明确限制了 morph 数量（可能是 `num_local_morphs=N` 更小的值）。

3. **过多自由度 → 训练集内精准，测试集（Main_Sequence）外大幅震荡**：
   类似经典过拟合。模型对 5kGreedyROM 的 5000 帧描述精准，但 Main_Sequence
   包含训练集外的姿势，模型外推时产生大量错误形变。

---

## 已修复（本次会话成果）

- **GPU TDR 修复**：`extra_ue_cmd_args: ["-d3dadapter=1"]` 加入 capture config
  + `ue_capture_mainseq.py` L524-525 读取该参数追加到 UE 命令行
- **chain_monitor.ps1**：自动化 train→capture→compare→report 链式执行脚本，
  位于 `workspace/chain_monitor.ps1`

---

## 下一步（见 Phase V 计划）

参见 `docs/plan/phase_V_plan.md`：核心动作是在 `model_overrides` 中加入
`num_local_morphs` 和 `num_global_morphs` 配置，将模型尺寸对齐 Refference 292 MB。
