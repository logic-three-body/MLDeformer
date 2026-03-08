# Milestone: Phase W kickoff (Global 256 + QC gate)

日期：2026-03-08
状态：**进行中 — W-1 训练已完成，验证链进行中**

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
| gt_compare | 进行中（1560 帧，~20 分钟） |

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

触发条件：**W-1 ssim < 0.91** → 按 A → B → C 顺序执行，每次完整验证链。  
如 W-1 ssim ≥ 0.91：进行闭环，frame 1054 问题记录为已知轻微缺陷。

---

## 四、Kickoff 阶段完成项

- [x] 切换 NMM flesh 模型配置：Global 256 morph targets
- [x] 增加 outputs.bin QC gate（p50_max > 30 cm 自动失败）
- [x] 增加 `report.outputs_bin_qc` 配置块
- [x] 编写 Phase W 计划文档

## 五、待闭环项

- [ ] gt_compare 完成，读取 W-1 ssim_mean
- [ ] 按 ssim 决策：≥0.91 闭环 / <0.91 启动 W-2A
- [ ] 记录最终指标，写入 Phase W 闭环里程碑
- [ ] 调查 frame 1054 上臂形变根因（per-frame ssim 热图）
