# Phase V 计划：NMM 架构调参 + 模型质量对齐

> **背景**：Phase U（2026-03-07）完成，两次 25k iter 训练均得 ssim≈0.660（失败）。
> 根因：我方训练模型 1680 MB，Epic Refference 292 MB，尺寸差 5.76×。
> NMM 局部形态键数量过多 → 过拟合 → 泛化性差。

---

## 目标

训练出的 `MLD_NMMl_flesh_upperBody` 满足：
- 文件大小接近 Refference（目标 ~292 MB ± 30 MB）
- `ssim_mean ≥ 0.83`（pipeline 阈值）
- 理想目标：`ssim_mean ≥ 0.91`（Refference 水准）

---

## V1：诊断当前模型参数（先查清楚，再改动）

### V1a：读取当前模型的 NMM 参数
在 UE Editor（或 Python 脚本）中打开 `MLD_NMMl_flesh_upperBody` 资产，
记录以下参数：
- `num_local_morphs`（或 `num_local_curves`）
- `num_global_morphs`
- 网络隐层维度
- 实际 morph delta 矩阵尺寸

### V1b：读取 Refference 模型的 NMM 参数
同上，对比两者架构差异。

**工具**：
```python
import unreal
asset = unreal.load_asset("/Game/Characters/Emil/Deformers/MLD_NMMl_flesh_upperBody")
model = asset.get_model()  # 取 NMM model
# 查看 model 属性：num_local_curves, num_global_curves, etc.
```

---

## V2：限制 NMM 形态键数量（核心修复）

### V2a：在 `model_overrides` 增加参数

修改 `config/pipeline.full_exec.yaml`，`deformer_assets.flesh.model_overrides`：

```yaml
model_overrides:
  num_iterations: 25000
  num_local_morphs: 64      # 待定，参考 Refference 实际值
  num_global_morphs: 16     # 待定
  # 可能还需要调整：
  # morph_targets_error_threshold: 0.01
```

> **注**：精确值需先通过 V1 诊断确认 Refference 使用的数量。
> 如果 Refference 用了 64 local + 16 global，我们加同样的约束。

### V2b：预期效果
- 限制 local morphs → 模型容量降低 → 尺寸接近 292 MB → 泛化性提高
- 训练时间不变（iter 数相同），但过拟合风险降低

---

## V3：重新训练 + 验证闭环

```powershell
$hou2ue = "D:\UE\Unreal Projects\MLDeformerSample\UE57\pipeline\hou2ue"
$cfg    = "$hou2ue\config\pipeline.full_exec.yaml"
& "$hou2ue\workspace\chain_monitor.ps1"   # 已包含 train→capture→compare→report
```

验收标准：
- 训练后模型大小 ~300 MB（±50 MB 接受）
- `ssim_mean ≥ 0.83`（最低通过线）
- 理想 `ssim_mean ≥ 0.91`

---

## V4（备选）：LBS-vs-LBS 管线健壮性验证

如果 V2 调参需要多轮摸索，先运行一次 LBS-vs-LBS 确认管线本身无误：

```yaml
# pipeline.full_exec.yaml
ue:
  ground_truth:
    capture:
      disable_ml_deformer_for_source: true   # 改为 true
```

预期：ssim ≈ 1.0（管线通过），证明唯一问题在 NMM 模型，排除其他干扰。

---

## 优先顺序

```
V1a/V1b 诊断（~30 min）
  → V2a 加 num_local_morphs 约束
  → V3 重新训练闭环（~3h）
  → 如通过 → 提交文档 + 合并
  → 如未通过 → 根据模型大小调整参数，重复 V2→V3
```

---

## 相关文件

| 文件 | 用途 |
|------|------|
| `config/pipeline.full_exec.yaml` | 训练参数修改位置 |
| `workspace/chain_monitor.ps1` | 自动化链式执行脚本 |
| `docs/memory/checkpoint-20260307-phase-U-complete-nmm-overfit.md` | Phase U 结论 |

---

## 关键历史数据参考

| Phase | 训练数据 | 模型大小 | ssim | 状态 |
|-------|---------|---------|------|-----|
| Refference（Epic） | 未知 | 292 MB | 0.9142 | ✅ 目标 |
| U v1/v2（5kGreedyROM，无架构约束） | 5000 frames，8.46 GB | 1680 MB | 0.660 | ❌ |
| T v2（smoke GC，单位错误） | 1001 frames，1.65 GB | — | 0.590 | ❌ |
| T v4（hero64，pose 覆盖不足） | ~460 frames，117 MB | 357 MB | 0.637 | ❌ |
