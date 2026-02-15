# UE5 MLDeformer 主链路导航（Train -> Infer -> Render）

> 文档角色：本文件是“导航总线”。

## 1. 一句话主链
`Editor Train` -> `Model Train/Load` -> `Runtime Tick` -> `MeshDeformer Enqueue` -> `Optimus/ComputeGraph Dispatch` -> `Groom DataInterface` -> `Shader/RDG`。

## 2. 图文架构入口
- 架构图文档：`docs/02_code_map/README_UE5_Architecture_Diagram_CN.md`

## 3. 深度解析入口（分层）
1. `docs/02_code_map/deep_dive/README_UE5_TopDown_Source_Atlas_CN.md`
2. `docs/02_code_map/deep_dive/README_L1_Module_Startup_CN.md`
3. `docs/02_code_map/deep_dive/README_L2_Editor_Train_CN.md`
4. `docs/02_code_map/deep_dive/README_L3_Runtime_Infer_CN.md`
5. `docs/02_code_map/deep_dive/README_L4_Engine_MeshDeformer_CN.md`
6. `docs/02_code_map/deep_dive/README_L5_Optimus_ComputeGraph_CN.md`
7. `docs/02_code_map/deep_dive/README_L6_DataInterface_Groom_CN.md`
8. `docs/02_code_map/deep_dive/README_L7_Shader_RDG_Profiling_CN.md`

## 4. 深度解析入口（逐行核心代码）
1. `docs/02_code_map/core_line_by_line/README_Core_LineByLine_Index_CN.md`
2. `docs/02_code_map/core_line_by_line/README_Core_01_MLDeformerComponent_CN.md`
3. `docs/02_code_map/core_line_by_line/README_Core_02_MLDeformerModelInstance_CN.md`
4. `docs/02_code_map/core_line_by_line/README_Core_03_NeuralMorphModelInstance_CN.md`
5. `docs/02_code_map/core_line_by_line/README_Core_04_NearestNeighborModelInstance_CN.md`
6. `docs/02_code_map/core_line_by_line/README_Core_05_OptimusDeformerInstance_CN.md`
7. `docs/02_code_map/core_line_by_line/README_Core_06_ComputeGraph_Dispatch_CN.md`
8. `docs/02_code_map/core_line_by_line/README_Core_07_GroomWriteDataInterface_CN.md`

## 5. 固定源码解析基线（函数级）
1. `FMLDeformerEditorToolkit::Train` / `HandleTrainingResult`。
2. `FMLDeformerEditorModel::Train` + `TrainModel<T>`。
3. `FNeuralMorphEditorModel::Train` / `LoadTrainedNetwork`。
4. `FNearestNeighborEditorModel::Train` / `OnPostTraining` / `LoadTrainedNetwork`。
5. `UMLDeformerComponent::TickComponent` -> `UMLDeformerModelInstance::Tick`。
6. `UNeuralMorphModelInstance::SetupInputs` / `Execute` / `NetworkInstance->Run()`。
7. `UNearestNeighborModelInstance::SetupInputs` / `Tick` / `RunNearestNeighborModel`。
8. `USkinnedMeshComponent::CreateMeshDeformerInstances` / `EnqueueWork`。
9. `UOptimusDeformer::Compile` / `CreateOptimusInstance`。
10. `UOptimusDeformerInstance::SetupFromDeformer` / `EnqueueWork`。
11. `FComputeGraphInstance::EnqueueWork` 与 `ComputeGraphWorker` 的 `GatherDispatchData`。
12. Groom: `DeformerGroomComponentSource.cpp`、`DeformerDataInterfaceGroom*.cpp`、`GroomDeformerBuilder.cpp`、`DeformerDataInterfaceGroom*.ush`。

## 6. 模型专题入口
- NMM：`docs/02_code_map/README_NMM_TheoryCode_CN.md`
- NNM：`docs/02_code_map/README_NNM_TheoryCode_CN.md`
- Groom：`docs/02_code_map/README_GroomDeformer_TheoryCode_CN.md`

## 7. 统一字段约定
1. 映射表字段：
`concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation`
2. 分层链路字段：
`layer | parent_symbol | child_symbol | file_path | thread_context | data_carrier | failure_point | probe`

## 8. 快速验收清单
1. 分层文档具备“入口符号 -> 下一层符号”映射。
2. 逐行文档具备“line_range -> code_focus -> probe”映射。
3. NMM/NNM/Groom 均覆盖训练链 + 推理链 + 关键数据结构。
4. 文档包含 `STAT_MLDeformerInference` 与 `TRACE_CPUPROFILER_EVENT_SCOPE` / `CSV_SCOPED_TIMING_STAT`。
5. 所有路径可在 `D:/UE/UnrealEngine` 定位。
