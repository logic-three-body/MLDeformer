# Plan: Phase W - challenge ssim >= 0.91 (align Epic Refference 0.9142)

## TL;DR
Phase V 稳定在 ssim=0.8999。Phase W 最终没有靠继续扩容 Global NMM 达标，而是在 W-3B 切换到 NNM 后闭环成功。  
最终隔离 smoke 结果：`ssim_mean=0.9960`，`ssim_p05=0.9929`，主瓶颈窗口 `0588–0597 / 0600–0699` 已被实质性修复。

## 基线
- Phase V：Global 128 morphs，207 MB，ssim=0.8999，loss=0.011，25k iter，~16 min
- Epic Refference：306 MB，ssim=0.9142
- 差距：1.43% absolute SSIM

## W-1 主实验：Global 256 morphs（已完成）

**假设**：
- 256 个全局形态基底可提升上臂等细节区域的变形捕获精度
- 全局 morphs 共享约束，过拟合风险低于 Local 模式

**配置（pipeline.full_exec.yaml）**：
```yaml
mode: global
global_num_morph_targets: 256
global_num_hidden_layers: 2
global_num_neurons_per_layer: 128
num_iterations: 25000
```

**W-1 结果**：
| 项目 | 值 |
|------|-----|
| 训练状态 | ✅ 完成（status: success） |
| ended_at | 2026-03-08T10:39:14Z |
| 模型大小 | 207.1 MB（uasset，UE 内部压缩） |
| 最终 loss | ~0.011 |
| gt_source_capture | ✅ 完成 |
| gt_compare | ✅ 完成 |
| ssim_mean | **0.9005** |
| 达标 | ❌ 未达标（目标 ≥ 0.91）|

**视觉质量问题（frame 1054）**：
> 上臂肌肉在特定姿态下与参考存在可感知的形变偏差。
- 位置：Main Sequence frame 1054 / 1560（约 67.6%）
- 问题：Global morphs 分布全身，上臂专属容量有限；网络宽度（128 neurons）预测精度受限

**上臂 / 脖颈重点观测帧（基于 W-2C gt_compare_report.json）**：

| 优先级 | 帧范围 | W-2C ssim_mean | 备注 |
|--------|--------|----------------|------|
| 🔴 最差群 | **0588 – 0597** | ~0.795 – 0.800（body_roi ~0.73） | 全序列最低连续帧群，上臂/脖颈形变集中区 |
| 🔴 最差窗口 | 0600 – 0699 | 0.8302 | 全程均值最低百帧窗口 |
| 🟡 次差窗口 | 0500 – 0599 | 0.8380 | 包含最差帧群 |
| 🟡 肩颈段 | 0100 – 0199 | 0.8462 | 脖颈/肩部动作集中，重点观察颈侧形变 |
| 🟢 对照（优良段） | 1200 – 1299 | 0.9735 | 用于确认基准渲染正确性 |

> **注**：`LS_NMM_Local` 渲染（`Saved/MovieRenders/LS_NMM_Local.*.png`）仅含帧 0000 – 0893，不覆盖 frame 1054。
> 新实验视觉对比优先检查 **frame 0588 – 0597**（最差群）与 **frame 0100 – 0199**（肩颈段）。

**决策门**：
- ssim ≥ 0.91 → Phase W 闭环，frame 1054 记录为已知轻微缺陷
- 0.83 ≤ ssim < 0.91 → 启动 W-2 架构调参（见下方）
- ssim < 0.83 → 回退 Phase V 128 morphs

---

## W-2A 备用调参（256 morphs + 256 neurons）——已完成

**配置**：`global_num_neurons_per_layer: 256`（128→256）

**W-2A 结果**：
| 项目 | 值 |
|------|-----|
| ended_at | 2026-03-08T13:35:42Z |
| ssim_mean | **0.9006**（vs W-1 0.9005，提升 +0.0001）|
| ssim_p05 | 0.8120 |
| ms_ssim | 0.8670 |
| psnr | 29.26 dB |
| 达标 | ❌ 未达标 |

> **关键结论**：neurons 翻倍提升几乎为零（δ = +0.0001）。morphs 和 neurons 均非瓶颈。
> 三次实验累计：Phase V(0.8999) → W-1(+0.0006) → W-2A(+0.0001) = **总提升 +0.0007**。
> 新假设：训练数据覆盖度（pose distribution）或 morph 数量需大幅增加才能送出改善。

---

## W-2B 备用调参（512 morphs ——**已完成**）

**动机**：全局 512 morphs 让上臂区域获得更多全知形态化，测试 morph 数量大幅增加对质量上限的影响。

```

**W-2B 结果**：
| 项目 | 值 |
|------|-----|
| ended_at | 2026-03-08T15:03:00Z |
| ssim_mean | **0.9000**（vs W-2A 0.9006，**下降 -0.0006**）|
| ssim_p05 | 0.8121 |
| ms_ssim | 0.8661 |
| psnr | 29.18 dB |
| 达标 | ❌ 未达标 |

> ⚠️ **退步原因**：512 morphs 在 25k iters 内收敛不足（欠拟合）。
> **四轮汇总**：Phase V(0.8999) → W-1(0.9005) → W-2A(0.9006) → W-2B(0.9000)
> **结论**：ssim 上限约 0.90，架构容量配置无关，根因需重新调查。

---

## W-2C 最终实验（256 morphs + 256 neurons + 50k iters——**已完成**）

> **重要背景**：这是 Phase W 中第一次先执行 `-Stage ue_setup` 的实验。W-1/W-2A/W-2B 均未重跑 ue_setup，实际沿用 Phase V 架构（128m/128n）训练。
> VRAM 证据：W-1/2A/2B = 1.14 GB（= Phase V），W-2C ue_setup 重跑后 = **1.79 GB**（确认 256 neurons 生效）。

**配置**：
```yaml
global_num_morph_targets: 256
global_num_neurons_per_layer: 256
num_iterations: 50000
```

**W-2C 结果**：
| 项目 | 值 |
|------|-----|
| ue_setup | success, ended_at: 2026-03-08T16:00:00Z（1.79 GB 确认）|
| ended_at | 2026-03-08T19:23:26Z |
| 最终 loss | ~0.00808（vs Phase V ~0.011，**-27%**）|
| ssim_mean | **0.9004**（vs W-2A 0.9006，-0.0002）|
| ssim_p05 | 0.8104 |
| ms_ssim | 0.8657 |
| psnr | **29.57 dB**（vs W-2A 29.26，**+0.31 dB**）|
| de2000 | **2.138**（vs W-2A 2.141，微幅改善）|
| edge_iou | 0.9208 |
| 达标 | ❌ 未达标（目标 ≥ 0.91）|

> **W-2C 关键结论**：
> - Loss 降低 27% 但 ssim 几乎不变 → **loss 与 ssim 解耦**。
> - Phase W 五轮实验（Phase V → W-2C）ssim 始终在 0.900–0.9006 区间震荡（振幅 0.0007）。
> - NMM Global 模式：morphs/neurons 容量、迭代次数均非 ssim 瓶颈。
> - **需要 W-3 策略转变（见下方）**。

---

## W-3 策略转变方向（评估中）

Phase W 结果汇总：

| 实验 | 实际架构 | ssim | 备注 |
|------|---------|------|------|
| Phase V | 128m/128n/25k | 0.8999 | 基准 |
| W-1 | 128m/128n/25k（ue_setup 未重跑）| 0.9005 | 实为 Phase V 重复 |
| W-2A | 128m/128n/25k（ue_setup 未重跑）| 0.9006 | 实为 Phase V 重复 |
| W-2B | 128m/128n/25k（ue_setup 未重跑）| 0.9000 | 实为 Phase V 重复 |
| W-2C | **256m/256n/50k**（ue_setup 正常）| **0.9004** | 首次真实实验 |
| 目标 | Epic Refference | **0.9142** | 差距 -0.0138 |

**W-3 焦点分析（基于 `phase_w_focus_analysis.md`，2026-03-09）**：
- 主瓶颈不是 frame 1054，而是 **0588 – 0597** 连续最差簇：`ssim_mean=0.7984`，`body_roi_ssim_mean=0.7313`
- 最差百帧窗口是 **0600 – 0699**：`ssim_mean=0.8302`，`body_roi_ssim_mean=0.7530`
- frame **1054** 实测 `ssim=0.8822`，明显高于最差簇，属于**次级视觉 QA 点**，不应继续作为主优化目标
- 结论：**不要再继续做 Global morphs / neurons / iterations 扩容试错**

**W-3 可能方向**：
1. **受限 Local 模式**：仅在显式 per-bone morph cap 下尝试局部容量，避免重回 Phase U 的 Local 过参数化失败
2. **NearestNeighborModel（NNM）**：基于相似姿态插值 → 可能缓解局部姿态覆盖不足问题
3. **训练数据分析**：检查 5kGreedyROM pose 分布，确认 frame 1054 类似姿态覆盖密度
4. **Ground truth 质量审查**：确认 gt_source 渲染本身是否存在 ssim 上限

**W-3A 推荐顺序**：
1. 先做受限 Local 或 NNM 准备，不再做新的 Global 扩容实验
2. 视觉回归优先检查 **0588 – 0597** 与 **0100 – 0199**
3. frame **1054** 仅保留为覆盖到该帧时的次级复核点

**W-3A 已完成验证（2026-03-09，失败）**：
```yaml
config: UE57/pipeline/hou2ue/config/pipeline.phase_w_w3a_local.yaml
run_dir: UE57/pipeline/hou2ue/workspace/runs/20260309_144941_smoke_w3a_local
mode: local
local_num_morph_targets_per_bone: 1
num_iterations: 25000
```

闭环结果：训练、`gt_reference_capture`、`gt_source_capture` 全部成功，但 `gt_compare` 指标严重退化，`ssim_mean=0.5550`、`ssim_p05=0.4389`、`psnr_mean=14.37`、`edge_iou_mean=0.4619`、`body_roi_ssim_mean=0.5181`，远低于 Phase W 阈值，也明显差于 W-2C 的 `ssim_mean≈0.9004`。

补充结论：`report` 阶段的 `outputs.bin` QC 仍然通过（`p50_max_cm=4.02 <= 30`），因此这次失败更接近**模型/架构退化**，而不是 smoke 数据或输出缓存质量问题。

> 该配置是“最小受限 Local”试探版：先显式限制每骨骼 morph 容量，再判断 Local 路线是否值得继续，而不是直接回到默认 Local。

> 现结论：`local_num_morph_targets_per_bone=1` 的 W-3A 可判定为**失败分支**，不应继续在该配置上追加训练时间；W-3 后续应优先转向 **NNM** 或更有根据的数据/GT 审查。

**W-3B 已验证成功（NNM）**：
```yaml
config: UE57/pipeline/hou2ue/config/pipeline.phase_w_w3b_nnm.yaml
run_dir: UE57/pipeline/hou2ue/workspace/runs/20260309_164800_smoke_w3b_nnm
asset_path: /Game/Characters/Emil/Deformers/MLD_NMMl_flesh_upperBody
model_type: NNM
neighbor_poses: /Game/Characters/Emil/Animation/MLD_train/upperBodyFlesh_5kGreedyROM
neighbor_meshes_template: /Game/Characters/Emil/GeomCache/MLD_Train/GC_upperBodyFlesh_5kGreedyROM
num_pca_coeffs: 64
num_basis_per_section: 64
num_iterations: 5000
```

已完成 `ue_setup`，隔离 `ue_setup_report.json` 显示 `flesh` 资产已按该配置切换为 `model_type=NNM`，训练输入解析到 `upperBodyFlesh_5kGreedyROM` / `GC_upperBodyFlesh_5kGreedyROM`。

该配置沿用当前已验证的 flesh 训练输入，只把 `flesh` 资产切换为单 section 的 NNM 试探版，用于检验“相似姿态插值”是否能改善 W-2C 在 **0588 – 0597 / 0600 – 0699** 的局部瓶颈。

训练阶段经历 2 次启动级失败后自动重试成功：前两次均在保存 checkpoint 前退出，第 3 次尝试完成训练并生成 `train_report.json`（`status=success`，`ended_at=2026-03-09T10:04:22Z`）。

隔离验证链也已完成：`gt_reference_capture`、`gt_source_capture`、`gt_compare`、`report` 全部 `success`。关键指标如下：

- `ssim_mean=0.9960`
- `ssim_p05=0.9929`
- `psnr_mean=52.28 dB`
- `psnr_min=44.69 dB`
- `edge_iou_mean=0.9942`
- `ms_ssim_mean=0.9979`
- `de2000_mean=0.2339`
- `body_roi_ssim_mean=0.9943`

这组结果不仅显著高于 W-2C（`ssim_mean≈0.9004`），也实质性修复了 W-3 关注窗口：`0500 – 0599` 提升到 `ssim_mean=0.9946`，`0600 – 0699` 提升到 `ssim_mean=0.9964`，说明此前的主瓶颈簇在 NNM 路线上已被覆盖。

另一个重要结论是：pipeline report 中的 `strict_thresholds_required`（`ssim_mean>=0.995`、`ssim_p05>=0.985`、`psnr_mean>=35`、`edge_iou>=0.97` 等）也全部满足，因此 W-3B 不只是“过线”，而是达到接近逐帧重合的 smoke 结果。

附注：`report.outputs_bin_qc` 仍指向 `Intermediate/NeuralMorphModel/outputs.bin`，该 QC 在 NNM 分支上不应作为主要判定依据；W-3B 的接受结论应以隔离 run dir 中真实完成的 capture/compare 指标为准。

---

## W-3 QC Gate（W-1 后独立验证）

目标：防止 smoke GC 数据质量问题重现。

实现状态：
- 已在 `build_report.py` report 阶段增加 QC gate
- 配置于 `report.outputs_bin_qc`，阈值 30.0 cm
- pipeline 失败时作为报告失败项输出

---

## 执行命令

```powershell
# 训练
& "D:/UE/Unreal Projects/MLDeformerSample/UE57/pipeline/hou2ue/run_all.ps1" `
  -Stage train `
  -Config "D:/UE/Unreal Projects/MLDeformerSample/UE57/pipeline/hou2ue/config/pipeline.full_exec.yaml" `
  -Profile smoke

# 验证链（隔离 run dir，顺序执行）
$cfg = "D:/UE/Unreal Projects/MLDeformerSample/UE57/pipeline/hou2ue/config/pipeline.phase_w_w3b_nnm.yaml"
$runDir = "D:/UE/Unreal Projects/MLDeformerSample/UE57/pipeline/hou2ue/workspace/runs/20260309_164800_smoke_w3b_nnm"

& "D:/UE/Unreal Projects/MLDeformerSample/UE57/pipeline/hou2ue/run_all.ps1" `
  -Stage gt_reference_capture `
  -Config $cfg `
  -Profile smoke `
  -RunDir $runDir

& "D:/UE/Unreal Projects/MLDeformerSample/UE57/pipeline/hou2ue/run_all.ps1" `
  -Stage gt_source_capture `
  -Config $cfg `
  -Profile smoke `
  -RunDir $runDir

& "D:/UE/Unreal Projects/MLDeformerSample/UE57/pipeline/hou2ue/run_all.ps1" `
  -Stage gt_compare `
  -Config $cfg `
  -Profile smoke `
  -RunDir $runDir

& "D:/UE/Unreal Projects/MLDeformerSample/UE57/pipeline/hou2ue/run_all.ps1" `
  -Stage report `
  -Config $cfg `
  -Profile smoke `
  -RunDir $runDir
```

---

## 验证检查项

1. train_report.json status = success
2. gt_compare ssim_mean ≥ 0.91（W-1 目标）
3. report 阶段 outputs.bin QC gate 通过（p50_max ≤ 30 cm）
4. **上臂 / 脖颈重点帧视觉确认**（参照 W-1 节"上臂 / 脖颈重点观测帧"表格）：
  - frame **0588 – 0597**：上臂/脖颈最差群，确认新实验是否比 W-2C 有改善
  - frame **0100 – 0199**：肩颈动作段，重点观察脖颈侧面与锁骨区形变
  - frame **1200 – 1299**：优良对照段，确认渲染无异常
  - frame **1054**：原始已知上臂问题帧（仅限覆盖该帧的渲染）
5. 已达标：以 W-3B NNM 结果作为 Phase W 闭环版本归档

---

## 相关文件

- `UE57/pipeline/hou2ue/config/pipeline.full_exec.yaml`
- `UE57/pipeline/hou2ue/config/pipeline.phase_w_w3a_local.yaml`
- `UE57/pipeline/hou2ue/scripts/build_report.py`
- `UE57/pipeline/hou2ue/scripts/analyze_phase_w_focus.py`
- `docs/milestones/milestone-20260309-phase-W-closure.md`
- `UE57/pipeline/hou2ue/workspace/latest/smoke/reports/phase_w_focus_analysis.md`
- `docs/milestones/milestone-20260308-phase-W-kickoff.md`
- `docs/plan/phase_W_plan.md`
