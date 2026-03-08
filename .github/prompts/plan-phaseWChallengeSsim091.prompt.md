# Plan: Phase W — 挑战 ssim ≥ 0.91（对齐 Epic Refference 0.9142）

## TL;DR
Phase V 已稳定于 ssim=0.8999。Phase W 目标：通过增加 Global 形态目标数量（256 → 可选 512）以及架构微调，挑战 ssim ≥ 0.91 对齐 Epic Refference 0.9142。推理延迟 profiling 暂缓，Houdini smoke GC 修复本期不做。

## 现状基线
- Phase V: Global 128 morphs, 207 MB, ssim=0.8999, loss=0.011, 25k iter, 16 min
- Epic Refference: 306 MB, ssim=0.9142（差距 1.43%）
- 制约因素：128 形态目标可能已是容量上限；需测试 256 是否带来质量收益而不引入过拟合

## W-1：Global 256 morphs（主实验）

**假设**：
- 128 → 207 MB；256 → 预估 ~414 MB（线性）
- 更多基底 → 更精细形变表达 → ssim 有望超过 0.91
- 风险：VRAM 压力上升；模型过大可能再次过拟合（但 Global 模式有全局约束，比 Local 安全）

**配置变更**（`pipeline.full_exec.yaml`）：
```yaml
model_overrides:
  mode: global
  global_num_morph_targets: 256   # ← 从 128 改为 256
  global_num_hidden_layers: 2
  global_num_neurons_per_layer: 128
  num_iterations: 25000
```

**决策门**：
- ssim ≥ 0.91 ✅ → Phase W 闭环，记录里程碑，合并 master
- 0.83 ≤ ssim < 0.91 → 进入 W-2 架构调参
- ssim < 0.83（退步）→ 回退 128 morphs，记录"128 是生产基线"

## W-2：架构调参（W-1 失败时的备选）

**选项 A**：增大网络宽度：`global_num_neurons_per_layer: 256`（原为 128）
**选项 B**：增加隐层：`global_num_hidden_layers: 3`（原为 2）
**选项 C**：两者组合（更大网络，训练时间可能增至 30+ min）

决策优先级：A → B → C，每个选项单独跑一次完整验证。

## W-3：GC QC 自动化门控（W-1 之后独立执行）

在 `pipeline/hou2ue/scripts/ue_import.py` 或 `houdini_export_abc.py` 中增加：
- 解析 `Intermediate/NeuralMorphModel/outputs.bin`
- 计算 per-frame max-abs 顶点偏移分布
- p50_max > 30 cm → pipeline 主动 FAIL，输出诊断信息

目的：防止 smoke GC 类问题（3/3 类历史失败根源）在未来重现。

## 执行命令

```powershell
$hou2ue = "D:\UE\Unreal Projects\MLDeformerSample\UE57\pipeline\hou2ue"
$cfg    = "$hou2ue\config\pipeline.full_exec.yaml"
# 修改 global_num_morph_targets 为 256 后执行：
& "$hou2ue\run_all.ps1" -Stage train -Config $cfg -Profile smoke
# 训练完成后运行验证链：
& "$hou2ue\run_all.ps1" -Stage gt_source_capture,gt_compare,report -Config $cfg -Profile smoke
```

## Relevant Files
- `UE57/pipeline/hou2ue/config/pipeline.full_exec.yaml` — 修改 global_num_morph_targets
- `UE57/pipeline/hou2ue/scripts/ue_import.py` — W-3 QC 门控
- `docs/milestones/` — 记录 Phase W 结果
- `docs/plan/phase_W_plan.md` — 存储本计划

## Verification
1. `train_report.json` → 模型大小 ~400 MB（合理范围内）
2. `gt_compare` → ssim_mean ≥ 0.91
3. 若达标：`git commit -m "feat: Phase W Global 256 morphs ssim≥0.91"`
4. 若未达标：记录结果，进入 W-2

## Decisions
- 推理延迟 profiling：本期**不做**（Phase V 模型已满足质量要求后再做）
- Houdini smoke GC 修复：本期**不做**（5kGreedyROM 可继续使用）
- 256 morphs 无效时：接受 0.8999 作为生产基线，不再追求更高（除非 W-2 有明确增益）
