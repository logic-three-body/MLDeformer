# Core-03: `NeuralMorphModelInstance.cpp` 逐行解析

## 1. 文件定位
- `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NeuralMorphModel/Source/NeuralMorphModel/Private/NeuralMorphModelInstance.cpp`

## 2. 关键行段解析
| line_range | code_focus | explanation | breakpoint_probe |
|---|---|---|---|
| 181-191 | `SetupInputs` 网络有效性检查 | 要求 `MorphNetwork` 和 `MainModel` 均有效，否则直接 `false`。 | 人为破坏网络资产验证快速失败 |
| 193-199 | 组件与兼容性检查 | `SkeletalMeshComponent`、`SkeletalMeshAsset`、`bIsCompatible` 必须通过。 | 断点看 `bIsCompatible` 来源 |
| 201-209 | 输入维度一致性 | 用 `CalcNumNeuralNetInputs` 对比网络输入维度，不一致直接中止。 | 改骨骼/曲线列表验证失败 |
| 211-214 | 输入填充 | `FillNetworkInputs()` 真正写入 NNE 输入张量。 | 断点验证输入已更新 |
| 217-228 | `Execute` 开场与空网络退化 | 统计打点后，若网络空则走 `Super::Execute`。 | 空网络模型下断点确认退化 |
| 232-237 | Morph 权重目标获取 | 通过 LOD 找 `FExternalMorphSetWeights`；失败直接返回。 | 非兼容 LOD 验证空指针保护 |
| 239-244 | `NetworkInstance` 容错 | 实例为空时将权重清零并返回。 | 手动置空实例，验证 `ZeroWeights()` |
| 249-258 | 输出维度二次校验 | `NumMorphTargets == NumNetworkWeights + 1` 才继续。`+1` 是均值 morph。 | 断点 254，验证维度断言 |
| 261 | 执行前向 | `NetworkInstance->Run()` 更新输出。 | 结合 CPU Trace 观察执行耗时 |
| 263-270 | 权重写回 | 均值槽位写 `ModelWeight`；其余槽位写 `NetworkOutput * ModelWeight`。 | 对比输出和最终权重一致性 |
| 272-280 | 训练分布外防护 | 开启时调用 `ClampMorphTargetWeights`，防止 OOD 输入导致权重爆炸。 | 极端姿态下验证 clamp 生效 |

## 3. 控制流总结
1. `SetupInputs` 负责“能不能跑”。
2. `Execute` 负责“跑完怎么写回”。
3. NMM 的稳定性关键在 201-209（输入维度）和 272-280（权重约束）。

## 4. 调试建议
1. 先看 201-209 是否因输入维度失败。
2. 再看 254 的 morph 数量一致性。
3. 性能分析直接看 `CSV_SCOPED_TIMING_STAT(MLDeformer, NeuralMorphExecute)`。
