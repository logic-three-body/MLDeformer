# NMM（Neural Morph Model）理论-源码深度映射

> 对应分层文档：
> - `docs/02_code_map/deep_dive/README_L2_Editor_Train_CN.md`
> - `docs/02_code_map/deep_dive/README_L3_Runtime_Infer_CN.md`
> - `docs/02_code_map/deep_dive/README_L7_Shader_RDG_Profiling_CN.md`

## 1. Top-Down 主链（NMM）
1. Editor：`FNeuralMorphEditorModel::Train`。
2. 训练桥：`TrainModel<UNeuralMorphTrainingModel>`。
3. 产物加载：`FNeuralMorphEditorModel::LoadTrainedNetwork`。
4. Runtime：`UMLDeformerComponent::TickComponent` -> `UMLDeformerModelInstance::Tick`。
5. NMM 分支：`UNeuralMorphModelInstance::SetupInputs` -> `UNeuralMorphModelInstance::Execute` -> `NetworkInstance->Run()`。
6. 输出写回：Morph 权重回填并执行安全约束（clamp）。

## 2. 训练链映射
| concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation |
|---|---|---|---|---|---|---|---|
| NMM 训练入口 | Morph weight regression training | NeuralMorphModelEditor | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NeuralMorphModel/Source/NeuralMorphModelEditor/Private/NeuralMorphEditorModel.cpp` | `FNeuralMorphEditorModel::Train` | train | 通过模板桥接进入 NMM 训练模型 | 训练返回 `Success` |
| 模板桥接 | Generic training abstraction | MLDeformerFrameworkEditor | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFrameworkEditor/Public/MLDeformerEditorModel.h` | `TrainModel<UNeuralMorphTrainingModel>` | train | 与具体训练实现解耦 | 训练模型缺失时返回失败 |
| 训练产物加载 | Trained network load | NeuralMorphModelEditor | `.../NeuralMorphEditorModel.cpp` | `FNeuralMorphEditorModel::LoadTrainedNetwork` | train | 从磁盘产物加载 NMM 网络对象用于推理 | 删除产物后应报错并终止 |

## 3. 推理链映射
| concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation |
|---|---|---|---|---|---|---|---|
| 推理总入口 | Runtime frame loop | MLDeformerFramework | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFramework/Private/MLDeformerComponent.cpp` | `UMLDeformerComponent::TickComponent` | infer | 每帧驱动模型实例执行 | `stat MLDeformer` 中有采样 |
| 统一调度 | Shared inference state machine | MLDeformerFramework | `.../MLDeformerModelInstance.cpp` | `UMLDeformerModelInstance::Tick` | infer | 检查权重/兼容性/输入有效性后才执行 | 权重设 0 进入回退 |
| NMM 输入准备 | Feature assembly | NeuralMorphModel | `.../NeuralMorphModelInstance.cpp` | `UNeuralMorphModelInstance::SetupInputs` | infer | 读取骨骼/曲线输入并写入网络输入缓冲 | 维度错配时应直接失败 |
| NMM 执行 | Neural forward pass | NeuralMorphModel | 同上 | `UNeuralMorphModelInstance::Execute` | infer | 执行网络并读取输出权重 | 进入 `CSV_SCOPED_TIMING_STAT` 采样 |
| 网络前向 | CPU runtime inference | NeuralMorphModel | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NeuralMorphModel/Source/NeuralMorphModel/Private/NeuralMorphNetwork.cpp` | `UNeuralMorphNetworkInstance::Run` | infer | 基于 NNE RuntimeBasic CPU 执行主/组网络 | NNE runtime 可正常获取 |
| 权重安全约束 | Output stabilization | NeuralMorphModel | `.../NeuralMorphModelInstance.cpp` | `ClampMorphTargetWeights` 调用路径 | infer | 防止 OOD 输出导致形变爆炸 | 极端姿态下不出现发散 |

## 4. 关键数据结构
| concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation |
|---|---|---|---|---|---|---|---|
| NMM 网络资产 | Compact runtime network | NeuralMorphModel | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NeuralMorphModel/Source/NeuralMorphModel/Public/NeuralMorphNetwork.h` | `UNeuralMorphNetwork` | both | 保存网络结构、权重和模型句柄 | 资产可序列化/反序列化 |
| NMM 网络实例 | Runtime tensor holder | NeuralMorphModel | 同上 | `UNeuralMorphNetworkInstance` | infer | 持有输入/输出张量与模型实例 | 张量维度与模型匹配 |
| NMM 运行实例 | MLDeformer model instance | NeuralMorphModel | `.../NeuralMorphModelInstance.h` | `UNeuralMorphModelInstance` | infer | 连接 MLDeformer 框架与 NMM 网络执行 | 每帧执行路径稳定 |

## 5. 分层链路表（NMM）
| layer | parent_symbol | child_symbol | file_path | thread_context | data_carrier | failure_point | probe |
|---|---|---|---|---|---|---|---|
| L2->L3 | `FNeuralMorphEditorModel::Train` | `FNeuralMorphEditorModel::LoadTrainedNetwork` | `.../NeuralMorphEditorModel.cpp` | GameThread(Editor) | 训练产物文件 | 产物不存在 | 手动删除产物验证失败 |
| L3 | `UMLDeformerModelInstance::Tick` | `UNeuralMorphModelInstance::SetupInputs` | `.../MLDeformerModelInstance.cpp` -> `.../NeuralMorphModelInstance.cpp` | GameThread | 输入特征缓冲 | 输入维度不一致 | 断点检查输入计数 |
| L3 | `UNeuralMorphModelInstance::Execute` | `UNeuralMorphNetworkInstance::Run` | `.../NeuralMorphModelInstance.cpp` -> `.../NeuralMorphNetwork.cpp` | GameThread | 输入/输出 tensor | NetworkInstance 为空 | 空网络资产验证保护 |
| L3->L7 | `UNeuralMorphModelInstance::Execute` | `CSV_SCOPED_TIMING_STAT(MLDeformer, NeuralMorphExecute)` | `.../NeuralMorphModelInstance.cpp` | GameThread/Profiler | CSV 统计 | 指标缺失 | 导出 CSV 验证指标 |

## 6. 常见失败模式
1. 训练成功但加载失败：产物路径或版本不一致。
2. 推理不执行：`ModelWeight` 太低、兼容性检查失败、`SetupInputs` 返回 false。
3. 输出不稳定：输入 OOD 或未经过权重约束。

## 7. 最小验证步骤
1. 完成训练后立即调用加载路径，确认网络对象有效。
2. 运行动画，确认 Morph 权重随姿态变化且无爆炸。
3. `stat MLDeformer` + CSV 同时采样，确认推理耗时稳定。
