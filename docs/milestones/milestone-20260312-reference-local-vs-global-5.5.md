# 里程碑：2026-03-12 Refference(UE5.5) Local vs Global 自对照

## 1. 目的

验证 **UE5.5 Refference 工程自身** 在同一 NMM flesh 资产、同一 smoke GT 对比流程下，`Local` 与 `Global` 两种模式的效果差异，判断：

1. `Global` 是否在 5.5 Refference 自身就已经明显退化。
2. UE5.7 当前异常是否更可能来自 **跨版本实现差异**，而不是“Global 模式天然更差”。

结论先行：**不是。** 在 5.5 Refference 自身里，`Global` 没有退化，反而比 `Local` 略好，且训练更快。

---

## 2. 实验设置

### 2.1 工程与引擎

- 工程：`D:/UE/Unreal Projects/MLDeformerSample/Refference/MLDeformerSample.uproject`
- 引擎：`D:/Program Files/Epic Games/UE_5.5/Engine/Binaries/Win64/UnrealEditor.exe`
- 资产：`/Game/Characters/Emil/Deformers/MLD_NMMl_flesh_upperBody`

### 2.2 对照原则

两组实验均使用：

- 同一 Refference 5.5 工程
- 同一 flesh 资产路径
- 同一训练输入：`upperBodyFlesh_5kGreedyROM` + `upperBodyFlesh_hero64`
- 同一 GT capture 流程
- 同一 smoke profile
- 同一 compare thresholds

唯一核心变量：

- Local 组：`Mode = Local`
- Global 组：`Mode = Global`

### 2.3 配置文件

- Local: `UE57/pipeline/hou2ue/workspace/generated_configs/pipeline.reference_refference_local.smoke.yaml`
- Global: `UE57/pipeline/hou2ue/workspace/generated_configs/pipeline.reference_refference_global.smoke.yaml`

### 2.4 Run 目录

- Local run: `UE57/pipeline/hou2ue/workspace/runs/20260312_refference_local_self_smoke`
- Global run: `UE57/pipeline/hou2ue/workspace/runs/20260312_refference_global_self_smoke`

### 2.5 Houdini 训练资产一致性复核

在进入 Local / Global 对照前，已对 Refference 与 UE57 两边的关键 Houdini 派生训练资产做文件级一致性校验，结果为 **大小与 SHA256 完全一致**：

- `GC_upperBodyFlesh_5kGreedyROM.uasset`
- `GC_upperBodyFlesh_hero64.uasset`
- `upperBodyFlesh_5kGreedyROM.uasset`
- `upperBodyFlesh_hero64.uasset`

这意味着本轮对照可以把“数据不一致”从根因候选里先排除掉。当前两边使用的是同一套 NMM flesh 训练输入，而不是“名字一样但内容不同”的 Houdini 资产。

---

## 3. 关键实现说明

为了让现有 pipeline 能直接驱动 Refference 5.5 工程，这次补齐了 Refference 的最小 C++ bridge：

- `SetupDeformerAsset`
- `TrainDeformerAsset`
- `EnsureModelType`

之前 Refference 5.5 仅暴露 `DumpDeformerSetup`，导致 `ue_setup_assets.py` 在 5.5 上直接失败：

- 失败原因：`setup_deformer_asset missing in MLDTrainAutomationLibrary`

这次补的是 **最小可用 bridge**，目标只覆盖本次实验所需的 NMM flesh setup/train 路径，不是把 UE57 的完整桥接原样搬回 5.5。

---

## 4. Local 组结果

### 4.1 训练

- 报告：`UE57/pipeline/hou2ue/workspace/runs/20260312_refference_local_self_smoke/reports/train_report.json`
- 状态：成功
- 训练耗时：`2975.8792 s`
- 训练结果：`training_result_code = 0`
- 网络加载：`true`

### 4.2 GT 对比

- 报告：`UE57/pipeline/hou2ue/workspace/runs/20260312_refference_local_self_smoke/reports/gt_compare_report.json`
- 状态：成功
- 帧数：`1560`

关键指标：

- `ssim_mean = 0.9909553`
- `ssim_p05 = 0.9513014`
- `psnr_mean = 50.4173`
- `edge_iou_mean = 0.9838588`
- `ms_ssim_mean = 0.9932878`
- `de2000_mean = 0.5799751`

---

## 5. Global 组结果

### 5.1 训练

- 报告：`UE57/pipeline/hou2ue/workspace/runs/20260312_refference_global_self_smoke/reports/train_report.json`
- 状态：成功
- 训练耗时：`1990.2504 s`
- 训练结果：`training_result_code = 0`
- 网络加载：`true`

### 5.2 GT 对比

- 报告：`UE57/pipeline/hou2ue/workspace/runs/20260312_refference_global_self_smoke/reports/gt_compare_report.json`
- 状态：成功
- 帧数：`1560`

关键指标：

- `ssim_mean = 0.9915689`
- `ssim_p05 = 0.9512772`
- `psnr_mean = 51.8201`
- `edge_iou_mean = 0.9846917`
- `ms_ssim_mean = 0.9934679`
- `de2000_mean = 0.5119898`

### 5.3 资产状态复核

- 复核 dump：`UE57/pipeline/hou2ue/workspace/runs/20260312_refference_global_self_smoke/reports/post_global_dump.json`
- 结果：`model_overrides_json.Mode = Global`
- 说明：Global 组并非“setup 报 success 但模式未实际切换”，资产状态已被明确验证。

---

## 6. Local vs Global 对比

以 `Global - Local` 计算：

- `ssim_mean`: `+0.0006136`
- `ssim_p05`: `-0.0000242`
- `psnr_mean`: `+1.4028`
- `edge_iou_mean`: `+0.0008329`
- `ms_ssim_mean`: `+0.0001801`
- `de2000_mean`: `-0.0680`
- `duration_sec`: `-985.6288`

解释：

- 绝大多数主指标中，`Global` 略优于 `Local`
- `ssim_p05` 有极小幅下降，但幅度可以忽略
- `de2000_mean` 更低，说明颜色差异更小
- 训练时间显著更短，约快 `16.4 min`

这说明在 **UE5.5 Refference 自身** 里：

- `Local` 和 `Global` 都是健康可用的
- `Global` 不是天然坏配置
- “换成 Global 就会明显坏掉” 这一假设不成立

---

## 7. 对 UE5.7 排查的含义

这次实验把问题边界进一步缩小了。

已经排除的方向：

1. 不是因为 Refference 资产在 5.5 下只有 Local 能工作、Global 本身就差。
2. 不是因为 Local/Global 两种模式在 Refference 5.5 自身存在明显质量断层。
3. 不是因为我们当前使用的 Refference 训练输入在 5.5 下不稳定。

因此，UE5.7 当前异常更应优先怀疑：

1. **UE5.5 与 UE5.7 的 Neural Morph 实现差异**
2. **跨版本默认行为差异**，尤其是未显式持久化但会影响训练/推理的内部状态
3. **同名字段相同，但内部解释或执行路径变化**
4. **不是 Houdini 训练数据内容不一致**，因为关键训练动画与 GeomCache 资产已经做过跨工程 hash 对齐验证

---

## 8. 对后续 UE5.7 的直接建议

建议下一轮按以下顺序排查：

1. 对比 UE5.5 / UE5.7 `NeuralMorphModel` 与 `NeuralMorphEditorModel` 的 `Local` / `Global` 训练路径实现。
2. 对比两版 `LoadTrainedNetwork`、输入维度更新、Morph 输出维度更新、推理输入组装路径。
3. 优先检查 `Local` 模式在 UE5.7 中是否存在实现变更，因为当前 UE5.5 Refference 的 `Local` 本身是健康的。
4. 把本次 5.5 Refference `Global` 结果作为额外基线，避免后续把“Global 略优”误判成异常噪声。

---

## 9. 本次结论

**最终结论：**

在 `Refference + UE5.5` 的原始环境里，`Local` 与 `Global` 两组都表现非常好，且 `Global` 略优于 `Local`。因此，当前 UE5.7 问题不能归因于“Refference 原本只有 Local 好用”或“Global 在基线环境下天然失真”。

对 UE5.7 的后续排查，应把重点转向：

- 引擎版本差异
- 非持久化内部状态
- 同字段不同执行语义
