# Milestone: Phase W kickoff (Global 256 + QC gate)

日期：2026-03-08  
状态：**✅ 已闭环：W-3B NNM smoke 验证成功（ssim_mean=0.9960）**

> 最新收口请优先阅读：`docs/milestones/milestone-20260309-phase-W-closure.md`

---

## 一、W-1 训练完成（2026-03-08 18:39）

| 参数 | 值 |
|------|-----|
| 模式 | `global` |
| `global_num_morph_targets` | **256**（Phase V 的 2× ）|
| `global_num_hidden_layers` | 2 |
| `global_num_neurons_per_layer` | 128 |
| `num_iterations` | 25000 |
| 最终 loss | ~0.011 |
| 模型大小（uasset）| **207.1 MB**（同 Phase V 128 morphs，UE 内部压缩所致） |
| 训练时长 | ~43 分钟（含 ArmouryCrate 导致的 2 次重试，有效训练约 41 分钟）|
| train_report.json | `status: success`，`ended_at: 2026-03-08T10:39:14Z` |
| gt_source_capture | `status: success`，`ended_at: 2026-03-08T10:48:01Z` |
| gt_compare | `status: success`，`ended_at: 2026-03-08T11:53:29Z` |

### W-1 质量指标（1560 帧）

| 指标 | W-1（256 morphs）| Phase V（128 morphs）| 变化 | 阈值 | 状态 |
|------|-----------------|---------------------|------|------|------|
| `ssim_mean` | **0.9005** | 0.8999 | +0.0006 | ≥ 0.91 | ❌ 未达标 |
| `ssim_p05` | **0.8122** | 0.8122 | 0 | ≥ 0.70 | ✅ |
| `psnr_mean` | **29.24 dB** | 29.15 dB | +0.09 | ≥ 22.0 | ✅ |
| `ms_ssim_mean` | **0.8664** | 0.8659 | +0.0005 | ≥ 0.80 | ✅ |
| `de2000_mean` | **2.144** | 2.156 | -0.012 | ≤ 8.0 | ✅ |
| `edge_iou_mean` | **0.9202** | 0.9200 | +0.0002 | ≥ 0.82 | ✅ |

> **关键观察**：256 morphs vs 128 morphs 的改善极其微小（δssim = +0.0006）。
> morphs 数量不是瓶颈，**网络宽度（neurons_per_layer = 128）是容量限制处**。
> → W-2A：将 `global_num_neurons_per_layer` 从 128 提升至 256。

### ArmouryCrate 崩溃记录（W-1 训练阶段）
| PID | 迭代范围 | 时长 | 备注 |
|-----|---------|------|------|
| PID 36600 | iter 0→4701 | 11.5 min | iter 4700 checkpoint 保存后退出 |
| PID 51708 | init crash | ~1 min | 采样后立即退出（GPU warmup 失败，无训练） |
| PID 23004 | iter 4700→22701 | ~39 min | iter 22700 checkpoint 后退出 |
| PID 22364 | iter 22700→25000 | ~4.5 min | 正常完成，模型加载成功 |

ArmouryCrate（ASUS GPU 超频工具）在 GPU 高负载约 5–12 分钟后应用 OC 配置，触发 CUDA kernel 错误导致 UE 退出。run_all.ps1 每次 retry 前 kill 相关进程，成功规避。

---

## 二、关键视觉观察（帧 1054）

> **用户观察**：在 `source` 与 `reference` 的第 1054 帧中，人物上臂肌肉有较为明显的变形差异，与参考相比存在可感知的形变偏差。

- **帧位置**：frame 1054 / 1560，位于 Main Sequence 中后段（约 67.6% 位置）
- **问题区域**：上臂（upper arm）肌肉变形
- **可能根因**：
  1. 全局 256 个 morphs 分布于整个上半身，上臂专属形态容量有限
  2. 网络宽度（128 neurons）对复杂上臂姿态的预测精度受限
  3. 训练数据中此类上臂极端姿态的覆盖密度不足

### W-2C 逐帧重点观测窗口

| 优先级 | 帧范围 | W-2C ssim_mean | 备注 |
|--------|--------|----------------|------|
| 🔴 最差群 | **0588 – 0597** | ~0.795 – 0.800（body_roi ~0.73） | 全序列最低连续帧群，上臂/脖颈形变集中区 |
| 🔴 最差窗口 | 0600 – 0699 | 0.8302 | 全程均值最低百帧窗口 |
| 🟡 次差窗口 | 0500 – 0599 | 0.8380 | 包含最差帧群 |
| 🟡 肩颈段 | 0100 – 0199 | 0.8462 | 脖颈/肩部动作集中，重点观察颈侧形变 |
| 🟢 对照（优良段） | 1200 – 1299 | 0.9735 | 用于确认基准渲染正确性 |

> `LS_NMM_Local` 渲染仅覆盖 0000 – 0893，不含 frame 1054。
> 后续视觉回归优先检查 0588 – 0597 与 0100 – 0199，再用 1200 – 1299 做正常段对照。

---

## 三、W-2 计划（上臂形变增强）

基于 frame 1054 观察 + W-1 ssim 结果（待 gt_compare 完成），制定如下调参序列：

| 实验 | 改动 | 假设 | 预期模型尺寸 |
|------|------|------|-------------|
| **W-2A** | `global_num_neurons_per_layer: 256`（128→256）| 更宽网络提升上臂姿态->形变权重的预测精度 | ~+10% 大小 |
| **W-2B** | `global_num_morph_targets: 512`（256→512）| 更多 morphs 允许上臂形态专门化 | ~+50% 大小 |
| **W-2C** | A + B 组合 | 最大容量配置 | ~+70% 大小 |

**W-1 ssim = 0.9005 < 0.91 → W-2A 已触发（2026-03-08）**

> 分析：morph 数翻倍效果微弱，瓶颈在网络容量（隐藏层宽度）。W-2A 增加 neurons_per_layer 128→256，预期提升上臂等细节区域的权重预测精度。

### W-2A 实测结果（2026-03-08 22:02 KST）

| 参数 | 值 |
|------|-----|
| 模式 | `global` |
| `global_num_morph_targets` | 256 |
| `global_num_hidden_layers` | 2 |
| `global_num_neurons_per_layer` | **256**（128→256 翻倍）|
| `num_iterations` | 25000 |
| train_report.json | `status: success`，`ended_at: 2026-03-08T13:35:42Z` |
| gt_compare | `status: success`，`ended_at: 2026-03-08T13:02:21Z` |

#### W-2A 质量指标（1560 帧）

| 指标 | W-2A（256 neurons）| W-1（128 neurons）| 变化 | 阈值 | 状态 |
|------|-----------------|---------------------|------|------|------|
| `ssim_mean` | **0.9006** | 0.9005 | +0.0001 | ≥ 0.91 | ❌ 未达标 |
| `ssim_p05` | **0.8120** | 0.8122 | -0.0002 | ≥ 0.70 | ✅ |
| `psnr_mean` | **29.26 dB** | 29.24 dB | +0.02 | ≥ 22.0 | ✅ |
| `ms_ssim_mean` | **0.8670** | 0.8664 | +0.0006 | ≥ 0.80 | ✅ |
| `de2000_mean` | **2.141** | 2.144 | -0.003 | ≤ 8.0 | ✅ |
| `edge_iou_mean` | **0.9211** | 0.9202 | +0.0009 | ≥ 0.82 | ✅ |

> **关键发现**：neurons_per_layer 翻倍（128→256）效果同样微弱（δssim = +0.0001）。
> **架构容量（morphs 数量、neurons 宽度）均非瓶颈。**
> 三阶段对比：Phase V(0.8999) → W-1(+0.0006) → W-2A(+0.0001)，合计提升仅 +0.0007。
> 下一假设：训练数据覆盖度（5kGreedyROM pose distribution）或 morph targets 数量需大幅增加（512）。
> → W-2B：`global_num_morph_targets` 256→512（neurons 256 保持）。

### W-2B 实测结果（2026-03-08 23:37 KST）

| 参数 | 值 |
|------|-----|
| 模式 | `global` |
| `global_num_morph_targets` | **512**（256→512 翻倍）|
| `global_num_hidden_layers` | 2 |
| `global_num_neurons_per_layer` | 256 |
| `num_iterations` | 25000 |
| train_report.json | `status: success`，`ended_at: 2026-03-08T15:03:00Z` |
| gt_compare | `status: success`，`ended_at: 2026-03-08T15:37:43Z` |

#### W-2B 质量指标（1560 帧）

| 指标 | W-2B（512 morphs）| W-2A（256 morphs）| W-1（256 morphs, 128n）| 变化 vs W-2A | 阈值 | 状态 |
|------|-----------------|---------------------|------|------|------|------|
| `ssim_mean` | **0.9000** | 0.9006 | 0.9005 | **-0.0006** | ≥ 0.91 | ❌ 未达标 |
| `ssim_p05` | **0.8121** | 0.8120 | 0.8122 | +0.0001 | ≥ 0.70 | ✅ |
| `psnr_mean` | **29.18 dB** | 29.26 dB | 29.24 dB | -0.08 | ≥ 22.0 | ✅ |
| `ms_ssim_mean` | **0.8661** | 0.8670 | 0.8664 | -0.0009 | ≥ 0.80 | ✅ |

> ⚠️ **W-2B 退步警告**：512 morphs 相比 256 morphs ssim 下降 -0.0006（0.9000 vs 0.9006）。
> 原因分析：更多 morph targets 在相同 25k iters 内收敛不足（欠拟合），导致轻微退步。
> 四轮实验汇总：Phase V(0.8999) → W-1(0.9005) → W-2A(0.9006) → W-2B(0.9000)。
> **结论：ssim 上限约在 0.90 附近，与架构容量配置无关**。根因可能是：
> 1. 训练数据（5kGreedyROM）pose 覆盖度不足
> 2. 需要更多训练迭代（25k → 50k）
> 3. 学习率策略或损失函数需调整

---

## 四、W-2C 实测结果（2026-03-09 04:23 KST）

> **重要背景**：W-2C 是 Phase W 中**首次真正执行 256 morphs + 256 neurons** 的实验。
> W-1/W-2A/W-2B 均仅跑 `-Stage train`，未重新执行 `-Stage ue_setup`，导致 UE 资产实际沿用 Phase V 架构（128 morphs, 128 neurons）。
> 证据：W-1/2A/2B GPU VRAM = **1.14 GB**（= Phase V）；W-2C ue_setup 重跑后 GPU = **1.79 GB**（= 256 neurons 实际应用）。

| 参数 | 值 |
|------|-----|
| 模式 | `global` |
| `global_num_morph_targets` | 256 |
| `global_num_hidden_layers` | 2 |
| `global_num_neurons_per_layer` | **256** |
| `num_iterations` | **50000** |
| ue_setup | `status: success`，`ended_at: 2026-03-08T16:00:00Z`（GPU 1.79 GB 确认）|
| train_report.json | `status: success`，`ended_at: 2026-03-08T19:23:26Z` |
| 最终 loss | ~0.00808（vs Phase V ~0.011，**低 27%**）|
| gt_source_capture | ✅ 完成 |
| gt_compare | ✅ 完成（1560 帧）|

#### W-2C 质量指标（1560 帧）

| 指标 | W-2C（256m/256n/50k）| W-2A（估计 128m/128n/25k）| W-2B（估计 128m/128n/25k）| Epic Ref | 阈值 | 状态 |
|------|----------------------|--------------------------|--------------------------|----------|------|------|
| `ssim_mean` | **0.9004** | 0.9006 | 0.9000 | **0.9142** | ≥ 0.91 | ❌ 未达标 |
| `ssim_p05` | **0.8104** | 0.8120 | 0.8121 | — | ≥ 0.70 | ✅ |
| `psnr_mean` | **29.57 dB** | 29.26 dB | 29.18 dB | — | ≥ 22.0 | ✅ (+0.31 dB) |
| `ms_ssim_mean` | **0.8657** | 0.8670 | 0.8661 | — | ≥ 0.80 | ✅ |
| `de2000_mean` | **2.138** | 2.141 | — | — | ≤ 8.0 | ✅ |
| `edge_iou_mean` | **0.9208** | 0.9211 | — | — | ≥ 0.82 | ✅ |

> **W-2C 关键结论**：
> - 256m/256n/50k 的 PSNR 提升显著（+0.31 dB），但 ssim 几乎原地踏步（+0.0005 vs Phase V）。
> - Loss 降低 27%（0.011 → 0.008）未能转化为 ssim 改善 → **loss 与 ssim 解耦**。
> - Phase W 五轮实验（Phase V → W-1 → W-2A → W-2B → W-2C）ssim 始终在 0.900–0.901 区间震荡。
> - **根本结论：NMM Global 模式架构容量（无论 128/256/512 morphs，128/256 neurons，25k/50k iters）均非 ssim 上限的瓶颈**。
> - 下一步需策略转变（W-3）：考虑 Local 模式 / NNM 模型 / 训练数据分布分析。

## 五、W-3 策略转变方向（评估中）

| 方向 | 目的 | 当前判断 |
|------|------|----------|
| 受限 Local 模式 | 为上臂/脖颈提供区域专属容量，同时避免默认 Local 的过参数化 | 优先级高 |
| NearestNeighborModel | 用相似姿态插值替代纯 Global NMM 容量扩展 | 优先级中 |
| 训练数据分析 | 核查 5kGreedyROM 对最差窗口姿态的覆盖密度 | 必做 |
| Ground truth 审查 | 确认 gt_source 渲染链本身没有质量上限 | 必做 |

### 2026-03-09 W-3 焦点分析补充

基于 `phase_w_focus_analysis.md` 的自动分析，W-3 结论进一步收紧：

| 项目 | 结果 | 结论 |
|------|------|------|
| 最差连续簇 | **0588 – 0597**，`ssim_mean=0.7984`，`body_roi_ssim_mean=0.7313` | 当前主瓶颈 |
| 最差百帧窗口 | **0600 – 0699**，`ssim_mean=0.8302` | 优先观察局部策略收益 |
| frame 1054 | `ssim=0.8822`，`body_roi_ssim=0.8143` | 已知缺陷，但不是主指标瓶颈 |
| Global 扩容 | 128m/128n/25k → 256m/256n/50k 后仍停在 0.900x | 应停止继续扫 Global 容量 |

> 这意味着 W-3A 不应理解为“切回默认 Local”。
> 正确含义是：**若做 Local，必须带显式 per-bone morph cap；否则优先转向 NNM。**

### 2026-03-09 W-3A 受限 Local 验证完成（失败）

已新增实验配置：`UE57/pipeline/hou2ue/config/pipeline.phase_w_w3a_local.yaml`

| 参数 | 值 |
|------|----|
| `mode` | `local` |
| `local_num_morph_targets_per_bone` | `1` |
| `num_iterations` | `25000` |
| `run_dir` | `UE57/pipeline/hou2ue/workspace/runs/20260309_144941_smoke_w3a_local` |
| 状态 | **训练/采集完成，gt_compare 失败** |

目的：先以最小局部容量验证 Local 路线是否有潜力改善 0588–0597 / 0600–0699 区段，而不直接回到默认 Local 的过参数化状态。

闭环结果：训练成功完成，且 `gt_reference_capture`、`gt_source_capture` 均成功，但最终 `gt_compare` 结果为：

| 指标 | W-3A |
|------|------|
| `ssim_mean` | `0.5550` |
| `ssim_p05` | `0.4389` |
| `psnr_mean` | `14.37` |
| `edge_iou_mean` | `0.4619` |
| `body_roi_ssim_mean` | `0.5181` |

判定：相比 W-2C `ssim_mean≈0.9004` 出现断崖式退化，说明当前“最小受限 Local”配置不是可行方向。

附注：`report` 阶段 `outputs.bin` QC 通过（`p50_max_cm=4.02`），因此失败更可能来自模型表达能力/架构路线，而非 smoke 数据质量问题。

### 2026-03-09 W-3B NNM 验证完成（成功）

已新增实验配置：`UE57/pipeline/hou2ue/config/pipeline.phase_w_w3b_nnm.yaml`

| 参数 | 值 |
|------|----|
| `asset_path` | `/Game/Characters/Emil/Deformers/MLD_NMMl_flesh_upperBody` |
| `model_type` | `NNM` |
| `run_dir` | `UE57/pipeline/hou2ue/workspace/runs/20260309_164800_smoke_w3b_nnm` |
| `neighbor_poses` | `/Game/Characters/Emil/Animation/MLD_train/upperBodyFlesh_5kGreedyROM` |
| `neighbor_meshes_template` | `/Game/Characters/Emil/GeomCache/MLD_Train/GC_upperBodyFlesh_5kGreedyROM` |
| `num_pca_coeffs` | `64` |
| `num_basis_per_section` | `64` |
| `num_iterations` | `5000` |
| `ue_setup` | **success**（隔离 run dir 已验证） |
| `train` | **success**（第 3 次自动重试成功） |
| `gt_reference_capture` | **success** |
| `gt_source_capture` | **success** |
| `gt_compare` | **success** |
| `report` | **success** |
| 状态 | **W-3B 验证成功，Phase W 已闭环** |

目的：沿用当前 flesh 训练输入，先验证 NNM 的“基础网络 + 近邻融合”两段式路径，判断它是否比 Global NMM 更能覆盖 0588–0597 / 0600–0699 的局部姿态瓶颈。

实际执行中，训练前两次尝试都在保存 checkpoint 前退出，`run_all.ps1` 自动重试后，第 3 次成功完成训练并加载网络。最终 `train_report.json` 显示 `ended_at=2026-03-09T10:04:22Z`，`model_type=NNM`，`training_result_code=0`。

最终 smoke 指标：

| 指标 | W-3B NNM |
|------|----------|
| `ssim_mean` | `0.9960` |
| `ssim_p05` | `0.9929` |
| `psnr_mean` | `52.28 dB` |
| `psnr_min` | `44.69 dB` |
| `edge_iou_mean` | `0.9942` |
| `ms_ssim_mean` | `0.9979` |
| `de2000_mean` | `0.2339` |
| `body_roi_ssim_mean` | `0.9943` |

关键窗口也已恢复：`0500–0599` 的 `ssim_mean=0.9946`，`0600–0699` 的 `ssim_mean=0.9964`。这说明 W-3 关注的主瓶颈簇在 NNM 路线上已被有效消除。

附注：`report.outputs_bin_qc` 仍引用 `Intermediate/NeuralMorphModel/outputs.bin`，因此在 NNM 分支上它只能作为旁证，主结论仍以隔离 run dir 中的 capture/compare 结果为准。

## 六、W-3 QC Gate

- `build_report.py` 已在 report 阶段增加 outputs.bin QC gate
- 配置入口：`report.outputs_bin_qc`
- 当前阈值：`p50_max <= 30.0 cm`
- 作用：避免 smoke GC 质量回退被误判为模型训练问题

---

## 七、Kickoff 阶段完成项

- [x] 切换 NMM flesh 模型配置：Global 256 morph targets
- [x] 增加 outputs.bin QC gate（p50_max > 30 cm 自动失败）
- [x] 增加 `report.outputs_bin_qc` 配置块
- [x] 编写 Phase W 计划文档

## 八、待闭环项

- [x] gt_compare 完成，W-1 ssim=0.9005（未达标）
- [x] W-2A 触发：`global_num_neurons_per_layer` 128→256
- [x] W-2A 训练完成（ssim=0.9006，未达标）
- [x] W-2A 验证链完成（gt_source + gt_compare）
- [x] W-2B 执行：`global_num_morph_targets` 256→512（ssim=0.9000，局部下降！）
- [x] W-2C 执行：256m/256n/50k iter，首次真正 ue_setup（ssim=0.9004，PSNR +0.31 dB）
- [x] ue_setup 重要性确认：W-1/2A/2B 实际均为 Phase V 架构（1.14 GB），W-2C 为 1.79 GB
- [x] W-3 焦点分析完成：确认 0588–0597 为主瓶颈簇，frame 1054 为次级 QA 点
- [x] W-3A 受限 Local 已闭环：训练+capture 完成，但 `ssim_mean=0.5550`，判定失败分支
- [x] W-3B NNM 已闭环：`pipeline.phase_w_w3b_nnm.yaml`，`ssim_mean=0.9960`
- [ ] 逐帧视觉复核：0588–0597、0100–0199、1200–1299；frame 1054 仅在覆盖时复核
- [x] W-3 策略转变决策：NNM 路线胜出，Phase W smoke 闭环达成
- [x] 记录最终指标并写回当前里程碑
