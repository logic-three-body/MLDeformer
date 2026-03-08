# Milestone: Phase W kickoff (Global 256 + QC gate)

日期：2026-03-08  
状态：**进行中 — W-2B 完成（ssim=0.9000，未达标），W-2C 待决策**

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

## 四、Kickoff 阶段完成项

- [x] 切换 NMM flesh 模型配置：Global 256 morph targets
- [x] 增加 outputs.bin QC gate（p50_max > 30 cm 自动失败）
- [x] 增加 `report.outputs_bin_qc` 配置块
- [x] 编写 Phase W 计划文档

## 五、待闭环项

- [x] gt_compare 完成，W-1 ssim=0.9005（未达标）
- [x] W-2A 触发：`global_num_neurons_per_layer` 128→256
- [x] W-2A 训练完成（ssim=0.9006，未达标）
- [x] W-2A 验证链完成（gt_source + gt_compare）
- [x] W-2B 执行：`global_num_morph_targets` 256→512（ssim=0.9000，局部下降！）
- [ ] 逐帧 ssim 分析（frame 1054 区域 1000–1100）
- [ ] W-2C / 数据培训策略决策会议
- [ ] 记录最终指标，写入 Phase W 闭环里程碑
