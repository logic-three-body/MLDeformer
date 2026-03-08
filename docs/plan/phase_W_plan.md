# Plan: Phase W - challenge ssim >= 0.91 (align Epic Refference 0.9142)

## TL;DR
Phase V 稳定在 ssim=0.8999。Phase W 目标 ssim ≥ 0.91，通过增加 NMM Global morph targets（128 → 256）实现。  
W-1 训练已完成（2026-03-08），frame 1054 上臂肌肉形变问题已记录，根据 ssim 结果决定是否启动 W-2。

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

**配置**：
```yaml
global_num_morph_targets: 512  # 256 → 512
global_num_neurons_per_layer: 256  # 保持 W-2A
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

## W-2C 备选（256 morphs + 256 neurons + 50k iters——**待决策**）

| 选项 | 改动 | 假设 | 条件 |
|------|------|------|------|
| **W-2C-迭代** | morphs=256, neurons=256, iters=50000 | 25k iters 不足以收敛到质量上限 | 已确认 |
| **W-2C-数据** | 检查 5kGreedyROM pose 覆盖度 | 训练数据缺乏 frame 1054 类似姿态 | 分析任务 |
| **W-2C-调度** | 调整学习率或损失函数权重 | 当前 loss 约 0.011-0.013 平台期，学习率策略受限 | 研究任务 |

> W-2B 退步意味着**更多 morphs 需要更多 iters**。优先尝试 W-2C-迭代（50k），成本约 90 分钟。

### 辅助调查（并行）：
- 提取 gt_compare 逐帧 ssim 数据，确认 frame 1054 区域（1000–1100）ssim 分布
- 检查 5kGreedyROM 训练集中上臂极端姿态覆盖密度
- 评估 p05 帧是否集中在上臂大幅运动区段

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

# 验证链（含 QC gate）
& "D:/UE/Unreal Projects/MLDeformerSample/UE57/pipeline/hou2ue/run_all.ps1" `
  -Stage gt_source_capture,gt_compare,report `
  -Config "D:/UE/Unreal Projects/MLDeformerSample/UE57/pipeline/hou2ue/config/pipeline.full_exec.yaml" `
  -Profile smoke
```

---

## 验证检查项

1. train_report.json status = success
2. gt_compare ssim_mean ≥ 0.91（W-1 目标）
3. report 阶段 outputs.bin QC gate 通过（p50_max ≤ 30 cm）
4. frame 1054 上臂形变差异主观可接受
5. 如达标：commit `feat: Phase W Global 256 morphs ssim>=0.91`

---

## 相关文件

- `UE57/pipeline/hou2ue/config/pipeline.full_exec.yaml`
- `UE57/pipeline/hou2ue/scripts/build_report.py`
- `docs/milestones/milestone-20260308-phase-W-kickoff.md`
- `docs/plan/phase_W_plan.md`
