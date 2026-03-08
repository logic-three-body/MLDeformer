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
| gt_compare | 进行中 |
| ssim_mean | **待定** |

**视觉质量问题（frame 1054）**：
> 上臂肌肉在特定姿态下与参考存在可感知的形变偏差。
- 位置：Main Sequence frame 1054 / 1560（约 67.6%）
- 问题：Global morphs 分布全身，上臂专属容量有限；网络宽度（128 neurons）预测精度受限

**决策门**：
- ssim ≥ 0.91 → Phase W 闭环，frame 1054 记录为已知轻微缺陷
- 0.83 ≤ ssim < 0.91 → 启动 W-2 架构调参（见下方）
- ssim < 0.83 → 回退 Phase V 128 morphs

---

## W-2 备用调参（仅在 W-1 未达 0.91 时执行）

### 聚焦问题：上臂形变精度不足（frame 1054 观察）

| 选项 | 改动 | 假设 | 预期影响 |
|------|------|------|---------|
| **W-2A（优先）** | `global_num_neurons_per_layer: 256` | 更宽网络提升上臂姿态预测精度 | 训练时间 +30%，模型 +10% |
| **W-2B** | `global_num_morph_targets: 512` | 更多 morphs 让上臂形态专门化 | 训练时间 +50%，模型 +50% |
| **W-2C** | A + B 组合 | 最大容量，对 frame 1054 问题最有效 | 训练时间 +80% |

每个选项均需完整验证链（train → gt_source_capture → gt_compare → report）。

### 辅助调查（W-2 期间并行）：
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
