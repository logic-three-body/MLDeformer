# UE5 ML Deformer 主链路源码映射（Train -> Infer）

本文固定 UE 版本基线为 `5.5`，并使用统一映射字段：
`concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation`

## 1. 训练入口链

| concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation |
|---|---|---|---|---|---|---|---|
| Editor 训练触发 | ML pipeline orchestration | MLDeformerFrameworkEditor | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFrameworkEditor/Private/MLDeformerEditorToolkit.cpp` | `FMLDeformerEditorToolkit::Train` | train | 统一处理预检查、训练执行、结果处理与刷新 | 点击编辑器 Train 按钮，观察日志和资产更新 |
| 训练策略分派 | Training abstraction | MLDeformerFrameworkEditor | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFrameworkEditor/Public/MLDeformerEditorModel.h` | `TrainModel<TrainingModelClass>` | train | 通过模板与派生 TrainingModel 连接 Python/Blueprint 训练实现 | 缺少派生类时应返回 `FailPythonError` |
| 模型级训练入口 | Model-specific training | NeuralMorph / NearestNeighbor / VertexDelta Editor | `.../NeuralMorphEditorModel.cpp`, `.../NearestNeighborEditorModel.cpp`, `.../VertexDeltaEditorModel.cpp` | `Train` | train | 各模型覆盖基础 Train，注入各自数据与后处理逻辑 | 比较不同模型 Train 返回码与产物 |

## 2. Runtime 推理主链

| concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation |
|---|---|---|---|---|---|---|---|
| 每帧推理入口 | Online inference loop | MLDeformerFramework | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFramework/Private/MLDeformerComponent.cpp` | `UMLDeformerComponent::TickComponent` | infer | 组件 Tick 中调用 ModelInstance，并统计 `STAT_MLDeformerInference` | `stat MLDeformer` 查看推理时间 |
| 基础实例调度 | Inference state machine | MLDeformerFramework | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFramework/Private/MLDeformerModelInstance.cpp` | `UMLDeformerModelInstance::Tick` | infer | 完成 post-init、输入准备、`Execute` 调用与 zero-weight 回退 | 将权重设为 0 验证 `HandleZeroModelWeight` 路径 |
| 输入装配 | Input feature construction | MLDeformerFramework | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFramework/Private/MLDeformerModelInstance.cpp` | `SetNeuralNetworkInputValues`, `SetBoneTransforms`, `SetCurveValues` | infer | 从骨骼与曲线读取输入并写入推理缓冲 | 验证骨骼/曲线数量与网络输入维度一致 |

## 3. 模型分支推理

| concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation |
|---|---|---|---|---|---|---|---|
| NMM 执行 | Morph-weight regression | NeuralMorphModel | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NeuralMorphModel/Source/NeuralMorphModel/Private/NeuralMorphModelInstance.cpp` | `SetupInputs`, `Execute` | infer | 网络运行后写回 Morph 权重并按训练范围 clamp | 异常输入下观察是否发生权重爆炸 |
| NNM 执行 | NN retrieval augmentation | NearestNeighborModel | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NearestNeighborModel/Source/NearestNeighborModel/Private/NearestNeighborModelInstance.cpp` | `SetupInputs`, `Execute`, `Tick` | infer | 先跑优化网络，再执行邻域模型融合细节 | 比较启停 NNM 时细节表现差异 |
| Vertex Delta 执行 | Direct delta path | VertexDeltaModel | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/VertexDeltaModel/Source/VertexDeltaModel/Private/VertexDeltaModelInstance.cpp` | `Execute` | infer | 作为早期模型分支，对照理解整体架构演进 | 仅作对照，不作为首轮重点 |

## 4. 训练产物加载（关键）
- NMM：`NeuralMorphEditorModel::LoadTrainedNetwork` 从 `onnx` 衍生 `nmn` 并加载 `UNeuralMorphNetwork`。
- NNM：`NearestNeighborEditorModel::LoadTrainedNetwork` 加载 `NearestNeighborModel.ubnne` 并初始化实例。
- VertexDelta：`VertexDeltaEditorModel::LoadTrainedNetwork` 将 onnx 读入 `UNNEModelData`。

## 5. 实操建议
1. 调试训练失败时先看 `TrainModel<>()` 返回码与模型 `Train` 预检查。
2. 调试推理异常时先看 `UMLDeformerModelInstance::Tick` 条件是否成立（兼容性、输入、权重）。
3. 始终把视觉结果与 `STAT_MLDeformerInference` 和内存数据一起看，避免只看单一指标。
