# Core-04: `NearestNeighborModelInstance.cpp` 逐行解析

## 1. 文件定位
- `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NearestNeighborModel/Source/NearestNeighborModel/Private/NearestNeighborModelInstance.cpp`

## 2. 关键行段解析（主路径）
| line_range | code_focus | explanation | breakpoint_probe |
|---|---|---|---|
| 37-42 | `Execute` | 执行优化网络实例 `OptimizedNetworkInstance->Run()`，并记录 CSV 计时。 | 断点 41 验证网络执行 |
| 44-54 | `SetupInputs` 模型状态检查 | 需要模型存在、输入信息有效、且 `IsReadyForInference()` 为 true。 | 在训练后未更新状态时验证失败 |
| 55-65 | 组件与网络实例检查 | 组件、mesh、兼容标志、优化网络与实例必须有效。 | 断点 62 看实例空分支 |
| 67-71 | 输入视图检查 | `GetInputView()` 失败则直接返回 false。 | 断点验证可写输入缓冲是否就绪 |
| 75-82 | 输入维度检查 | 与资产输入配置不一致时拒绝执行。 | 改输入配置触发失败路径 |
| 84-87 | 填充 + 裁剪 | 先写输入，再 `ClipInputs()` 抑制 OOD。 | 打印裁剪前后值对比 |
| 91-99 | `Tick` 后初始化补偿 | 与基类类似，后初始化未完成时重试。 | 首帧断点验证 |
| 101-108 | `Tick` 主分支 | 条件满足时顺序执行 `Execute` + `RunNearestNeighborModel`。 | 断点 106/107 验证双阶段执行 |
| 110-113 | 回退路径 | 条件不满足时 `HandleZeroModelWeight()`。 | 权重置 0 验证 |
| 115-117 | 后处理钩子 | `PostTick` 做统一收尾。 | 断点看 `bExecuteCalled` |

## 3. 关键行段解析（邻域融合）
| line_range | code_focus | explanation | breakpoint_probe |
|---|---|---|---|
| 358-367 | `RunNearestNeighborModel` 开场 | 读取模型与衰减系数 `DecayCoeff`。 | 断点检查衰减参数 |
| 370-375 | 目标权重表获取 | 按 LOD 找 `WeightData`，失败直接返回。 | 非法 LOD 验证 |
| 381-387 | 网络输出视图获取 | 输出视图缺失时清零权重并返回。 | 人为制造输出缺失验证 |
| 393-401 | 形状与状态重置 | 核对输出维度，必要时重置 `PreviousWeights`。 | 首次运行与热切换对比 |
| 405-411 | 网络权重写入 | 先写基础网络输出到 morph 权重。 | 比对输出数组与写回槽位 |
| 413-420+ | 分 section 邻域融合 | 按 section 计算邻域/权重更新（含 RBF 或最近邻策略）。 | 断点 section 循环，验证 neighbor id |
| 225-228 | `GetNearestNeighborIds` | Editor 调试可直接取邻域 id。 | 可视化当前邻域选择结果 |

## 4. 控制流总结
1. NNM = 基础网络输出 + 邻域融合二段式。
2. 稳定性关键在 `ClipInputs`、维度检查、`PreviousWeights` 衰减更新。
3. 视觉细节提升主要来自 413+ 的 section 级融合。

## 5. 调试建议
1. 先确认是否进入 107 行 `RunNearestNeighborModel`。
2. 若细节无提升，重点检查 413+ 的 section 是否 `IsReadyForInference()`。
3. 配合 `GetNearestNeighborIds()` 验证邻域选择是否符合预期。
