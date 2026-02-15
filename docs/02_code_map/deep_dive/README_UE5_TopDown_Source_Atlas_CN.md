# UE5 源码自顶向下总览（Top-Down Source Atlas）

> 基线：`EngineAssociation = 5.5`，`UE_ROOT = D:/UE/UnrealEngine`。
> 
> 目标：把 MLDeformer + Groom 从“模块启动”一直串到“Shader/RDG 执行与观测”。

## 1. 阅读顺序（建议严格按层）
1. `README_L1_Module_Startup_CN.md`
2. `README_L2_Editor_Train_CN.md`
3. `README_L3_Runtime_Infer_CN.md`
4. `README_L4_Engine_MeshDeformer_CN.md`
5. `README_L5_Optimus_ComputeGraph_CN.md`
6. `README_L6_DataInterface_Groom_CN.md`
7. `README_L7_Shader_RDG_Profiling_CN.md`

## 2. 跨层调用总图（从上到下）
1. 模块注册：`IMPLEMENT_MODULE(...)` + `StartupModule()` 把功能挂入编辑器/运行时。
2. Editor 训练入口：`FMLDeformerEditorToolkit::Train`。
3. 模型训练分派：`FMLDeformerEditorModel::Train` -> `TrainModel<T>` -> 各模型 `Train`。
4. Runtime 推理入口：`UMLDeformerComponent::TickComponent` -> `UMLDeformerModelInstance::Tick`。
5. 模型执行：NMM/NNM 的 `SetupInputs` + `Execute`/`RunNearestNeighborModel`。
6. Engine 集成：`USkinnedMeshComponent` 创建 `UMeshDeformerInstance` 并 `EnqueueWork`。
7. Optimus/ComputeGraph：`UOptimusDeformer::Compile` / `CreateOptimusInstance` -> `FComputeGraphInstance::EnqueueWork` -> `ComputeGraphWorker`。
8. Groom 数据接口：`UOptimusGroom*DataInterface` + `FOptimusGroom*DataProviderProxy`。
9. Shader/RDG：`DeformerDataInterfaceGroom*.ush` 读写模板 + RDG 参数分发。

## 3. 七层分解与主文档
| 层级 | 关注点 | 文档 |
|---|---|---|
| L1 | 模块启动与系统装配 | `docs/02_code_map/deep_dive/README_L1_Module_Startup_CN.md` |
| L2 | Editor 训练链（Train） | `docs/02_code_map/deep_dive/README_L2_Editor_Train_CN.md` |
| L3 | Runtime 推理链（Infer） | `docs/02_code_map/deep_dive/README_L3_Runtime_Infer_CN.md` |
| L4 | Engine MeshDeformer 集成 | `docs/02_code_map/deep_dive/README_L4_Engine_MeshDeformer_CN.md` |
| L5 | Optimus / ComputeGraph 调度 | `docs/02_code_map/deep_dive/README_L5_Optimus_ComputeGraph_CN.md` |
| L6 | Groom DataInterface 机制 | `docs/02_code_map/deep_dive/README_L6_DataInterface_Groom_CN.md` |
| L7 | Shader / RDG / Profiling | `docs/02_code_map/deep_dive/README_L7_Shader_RDG_Profiling_CN.md` |

## 4. 分层链路表（统一字段）
`layer | parent_symbol | child_symbol | file_path | thread_context | data_carrier | failure_point | probe`

| layer | parent_symbol | child_symbol | file_path | thread_context | data_carrier | failure_point | probe |
|---|---|---|---|---|---|---|---|
| L2->L3 | `FMLDeformerEditorToolkit::Train` | `FNeuralMorphEditorModel::LoadTrainedNetwork` | `Engine/Plugins/Animation/MLDeformer/.../MLDeformerEditorToolkit.cpp` | GameThread(Editor) | 训练产物（onnx/nmn/ubnne） | 模型文件缺失、架构不匹配 | 训练后强制重载网络，观察错误日志 |
| L3->L4 | `UMLDeformerModelInstance::Tick` | `USkinnedMeshComponent::CreateMeshDeformerInstances` | `Engine/Plugins/Animation/MLDeformer/.../MLDeformerModelInstance.cpp` + `Engine/Source/Runtime/Engine/Private/Components/SkinnedMeshComponent.cpp` | GameThread -> RenderEnqueue | 姿态输入、输出缓冲描述 | LOD 切换时实例失配 | 强制切 LOD，确认实例映射稳定 |
| L4->L5 | `UMeshDeformerInstance::EnqueueWork` | `FComputeGraphInstance::EnqueueWork` | `Engine/Source/Runtime/Engine/Classes/Animation/MeshDeformerInstance.h` + `Engine/Plugins/Runtime/ComputeFramework/.../ComputeGraphInstance.cpp` | GameThread -> RenderThread | DataProvider RenderProxy | DataProvider 无效 | 命中 FallbackDelegate 验证降级 |
| L5->L6 | `UOptimusDeformerInstance::EnqueueWork` | `UOptimusGroomDataInterface::CreateDataProvider` | `Engine/Plugins/Animation/DeformerGraph/.../OptimusDeformerInstance.cpp` + `Engine/Plugins/Runtime/HairStrands/.../DeformerDataInterfaceGroom.cpp` | RenderThread | Groom 绑定组件 + Dispatch 参数 | 绑定组件为空 | `IsValid()` 返回 false 分支 |
| L6->L7 | `FOptimusGroomWriteDataProviderProxy::GatherDispatchData` | `DeformerDataInterfaceGroomWrite.ush` 写回函数 | `Engine/Plugins/Runtime/HairStrands/.../DeformerDataInterfaceGroomWrite.cpp` + `.ush` | RenderThread/RDG | SRV/UAV + 参数结构体 | 输出流越界、维度不一致 | 打开 GPU 调试验证写回缓冲 |

## 5. 验证入口（建议先跑通）
1. `stat MLDeformer`：确认 `STAT_MLDeformerInference` 有稳定采样。
2. `TRACE_CPUPROFILER_EVENT_SCOPE`：在 `TickComponent` / `Execute` 上抓 CPU 时间片。
3. 对 NMM/NNM 各跑一次：确认训练产物可加载，Runtime 无输入维度异常。
4. 对 Groom 图做最小位移写回：确认 `.ush` 写回链路生效。

## 6. 与原映射文档的关系
- 本目录用于“层级剖析”。
- 具体模型细节请回看：
  - `docs/02_code_map/README_NMM_TheoryCode_CN.md`
  - `docs/02_code_map/README_NNM_TheoryCode_CN.md`
  - `docs/02_code_map/README_GroomDeformer_TheoryCode_CN.md`

## 7. 逐行核心解析入口
- `docs/02_code_map/core_line_by_line/README_Core_LineByLine_Index_CN.md`
