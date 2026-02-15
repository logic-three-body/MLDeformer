# 源码与符号索引（UE5.5 / Top-Down 版本）

> 基线：`UE_ROOT = D:/UE/UnrealEngine`，`EngineAssociation = 5.5`。

## 1. 层级索引

### L1 模块启动
| 层 | 文件 | 关键符号 | 验证命令 |
|---|---|---|---|
| L1 | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFramework/Private/MLDeformerModule.cpp` | `FMLDeformerModule::StartupModule` | `rg -n "FMLDeformerModule::StartupModule" "D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer"` |
| L1 | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFrameworkEditor/Private/MLDeformerEditorModule.cpp` | `FMLDeformerEditorModule::StartupModule` | `rg -n "FMLDeformerEditorModule::StartupModule" "D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer"` |
| L1 | `D:/UE/UnrealEngine/Engine/Plugins/Animation/DeformerGraph/Source/OptimusCore/Private/OptimusCoreModule.cpp` | `FOptimusCoreModule::StartupModule` | `rg -n "FOptimusCoreModule::StartupModule" "D:/UE/UnrealEngine/Engine/Plugins/Animation/DeformerGraph"` |
| L1 | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/ComputeFramework/Source/ComputeFramework/Private/ComputeFrameworkModule.cpp` | `FComputeFrameworkModule::StartupModule` | `rg -n "FComputeFrameworkModule::StartupModule" "D:/UE/UnrealEngine/Engine/Plugins/Runtime/ComputeFramework"` |

### L2 训练链
| 层 | 文件 | 关键符号 | 验证命令 |
|---|---|---|---|
| L2 | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFrameworkEditor/Private/MLDeformerEditorToolkit.cpp` | `FMLDeformerEditorToolkit::Train` / `HandleTrainingResult` | `rg -n "FMLDeformerEditorToolkit::Train|HandleTrainingResult" "D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer"` |
| L2 | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFrameworkEditor/Private/MLDeformerEditorModel.cpp` | `FMLDeformerEditorModel::Train` | `rg -n "FMLDeformerEditorModel::Train" "D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer"` |
| L2 | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NeuralMorphModel/Source/NeuralMorphModelEditor/Private/NeuralMorphEditorModel.cpp` | `FNeuralMorphEditorModel::Train` / `LoadTrainedNetwork` | `rg -n "FNeuralMorphEditorModel::Train|FNeuralMorphEditorModel::LoadTrainedNetwork" "D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer"` |
| L2 | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NearestNeighborModel/Source/NearestNeighborModelEditor/Private/NearestNeighborEditorModel.cpp` | `FNearestNeighborEditorModel::Train` / `OnPostTraining` / `LoadTrainedNetwork` | `rg -n "FNearestNeighborEditorModel::Train|OnPostTraining|LoadTrainedNetwork" "D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer"` |

### L3 推理链
| 层 | 文件 | 关键符号 | 验证命令 |
|---|---|---|---|
| L3 | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFramework/Private/MLDeformerComponent.cpp` | `UMLDeformerComponent::TickComponent` | `rg -n "UMLDeformerComponent::TickComponent" "D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer"` |
| L3 | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFramework/Private/MLDeformerModelInstance.cpp` | `UMLDeformerModelInstance::Tick` | `rg -n "UMLDeformerModelInstance::Tick" "D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer"` |
| L3 | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NeuralMorphModel/Source/NeuralMorphModel/Private/NeuralMorphModelInstance.cpp` | `UNeuralMorphModelInstance::SetupInputs` / `Execute` | `rg -n "UNeuralMorphModelInstance::SetupInputs|UNeuralMorphModelInstance::Execute" "D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer"` |
| L3 | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NearestNeighborModel/Source/NearestNeighborModel/Private/NearestNeighborModelInstance.cpp` | `UNearestNeighborModelInstance::Tick` / `RunNearestNeighborModel` | `rg -n "UNearestNeighborModelInstance::Tick|RunNearestNeighborModel" "D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer"` |

### L4 Engine MeshDeformer
| 层 | 文件 | 关键符号 | 验证命令 |
|---|---|---|---|
| L4 | `D:/UE/UnrealEngine/Engine/Source/Runtime/Engine/Private/Components/SkinnedMeshComponent.cpp` | `CreateMeshDeformerInstances` / `EnqueueWork` | `rg -n "CreateMeshDeformerInstances|EnqueueWork" "D:/UE/UnrealEngine/Engine/Source/Runtime/Engine/Private/Components/SkinnedMeshComponent.cpp"` |
| L4 | `D:/UE/UnrealEngine/Engine/Source/Runtime/Engine/Private/SkeletalRenderGPUSkin.cpp` | `ESkeletalMeshGPUSkinTechnique::MeshDeformer` 分支 | `rg -n "MeshDeformer|GetMeshDeformerInstanceForLOD" "D:/UE/UnrealEngine/Engine/Source/Runtime/Engine/Private/SkeletalRenderGPUSkin.cpp"` |
| L4 | `D:/UE/UnrealEngine/Engine/Source/Runtime/Engine/Classes/Animation/MeshDeformerInstance.h` | `UMeshDeformerInstance::EnqueueWork` | `rg -n "class UMeshDeformerInstance|EnqueueWork" "D:/UE/UnrealEngine/Engine/Source/Runtime/Engine/Classes/Animation/MeshDeformerInstance.h"` |

### L5 Optimus / ComputeGraph
| 层 | 文件 | 关键符号 | 验证命令 |
|---|---|---|---|
| L5 | `D:/UE/UnrealEngine/Engine/Plugins/Animation/DeformerGraph/Source/OptimusCore/Private/OptimusDeformer.cpp` | `UOptimusDeformer::Compile` / `CreateOptimusInstance` | `rg -n "UOptimusDeformer::Compile|CreateOptimusInstance" "D:/UE/UnrealEngine/Engine/Plugins/Animation/DeformerGraph/Source/OptimusCore/Private/OptimusDeformer.cpp"` |
| L5 | `D:/UE/UnrealEngine/Engine/Plugins/Animation/DeformerGraph/Source/OptimusCore/Private/OptimusDeformerInstance.cpp` | `SetupFromDeformer` / `EnqueueWork` | `rg -n "SetupFromDeformer|EnqueueWork" "D:/UE/UnrealEngine/Engine/Plugins/Animation/DeformerGraph/Source/OptimusCore/Private/OptimusDeformerInstance.cpp"` |
| L5 | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/ComputeFramework/Source/ComputeFramework/Private/ComputeGraphInstance.cpp` | `FComputeGraphInstance::EnqueueWork` | `rg -n "FComputeGraphInstance::EnqueueWork" "D:/UE/UnrealEngine/Engine/Plugins/Runtime/ComputeFramework"` |
| L5 | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/ComputeFramework/Source/ComputeFramework/Private/ComputeGraphWorker.cpp` | `GatherDispatchData` 调用链 | `rg -n "GatherDispatchData" "D:/UE/UnrealEngine/Engine/Plugins/Runtime/ComputeFramework/Source/ComputeFramework/Private/ComputeGraphWorker.cpp"` |

### L6 Groom DataInterface
| 层 | 文件 | 关键符号 | 验证命令 |
|---|---|---|---|
| L6 | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Source/HairStrandsDeformer/Private/DeformerGroomComponentSource.cpp` | `GetExecutionDomains` / `GetComponentElementCountsForExecutionDomain` | `rg -n "GetExecutionDomains|GetComponentElementCountsForExecutionDomain" "D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Source/HairStrandsDeformer/Private/DeformerGroomComponentSource.cpp"` |
| L6 | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Source/HairStrandsDeformer/Private/DeformerDataInterfaceGroom.cpp` | `CreateDataProvider` / `AllocateResources` / `GatherDispatchData` | `rg -n "CreateDataProvider|AllocateResources|GatherDispatchData" "D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Source/HairStrandsDeformer/Private/DeformerDataInterfaceGroom.cpp"` |
| L6 | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Source/HairStrandsDeformer/Private/DeformerDataInterfaceGroomGuide.cpp` | `CreateDataProvider` / `AllocateResources` / `GatherDispatchData` | `rg -n "CreateDataProvider|AllocateResources|GatherDispatchData" "D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Source/HairStrandsDeformer/Private/DeformerDataInterfaceGroomGuide.cpp"` |
| L6 | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Source/HairStrandsDeformer/Private/DeformerDataInterfaceGroomExec.cpp` | `GetDispatchThreadCount` / `GatherDispatchData` | `rg -n "GetDispatchThreadCount|GatherDispatchData" "D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Source/HairStrandsDeformer/Private/DeformerDataInterfaceGroomExec.cpp"` |
| L6 | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Source/HairStrandsDeformer/Private/DeformerDataInterfaceGroomWrite.cpp` | `CreateDataProvider` / `AllocateResources` / `GatherDispatchData` | `rg -n "CreateDataProvider|AllocateResources|GatherDispatchData" "D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Source/HairStrandsDeformer/Private/DeformerDataInterfaceGroomWrite.cpp"` |

### L7 Shader / Profiling
| 层 | 文件 | 关键符号 | 验证命令 |
|---|---|---|---|
| L7 | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Shaders/Private/DeformerDataInterfaceGroom.ush` | `Read*` | `rg --files -g "*DeformerDataInterfaceGroom*.ush" "D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands"` |
| L7 | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Shaders/Private/DeformerDataInterfaceGroomWrite.ush` | `Write*` | 同上 |
| L7 | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFramework/Public/MLDeformerModelInstance.h` | `STAT_MLDeformerInference` 声明 | `rg -n "STAT_MLDeformerInference" "D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer"` |
| L7 | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NeuralMorphModel/Source/NeuralMorphModel/Private/NeuralMorphModelInstance.cpp` | `CSV_SCOPED_TIMING_STAT(MLDeformer, NeuralMorphExecute)` | `rg -n "CSV_SCOPED_TIMING_STAT\(MLDeformer" "D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer"` |
| L7 | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NearestNeighborModel/Source/NearestNeighborModel/Private/NearestNeighborModelInstance.cpp` | `CSV_SCOPED_TIMING_STAT(MLDeformer, NearestNeighborExecute)` | 同上 |

## 2. 附加资料入口
- 理论总览：`docs/01_theory/README_MLDeformer_Groom_Theory_CN.md`
- 总链路导航：`docs/02_code_map/README_UE5_CodeMap_Mainline_CN.md`
- 分层深度解析：`docs/02_code_map/deep_dive/README_UE5_TopDown_Source_Atlas_CN.md`
- 参考库入口：`docs/references` 已移除（当前仓库不再内置参考子库）。

## 3. 行号漂移维护策略
1. 先按 `symbol` 搜索，再用行号定位。
2. 优先保持符号名稳定，不把文档绑定死到单个行号。
3. 升级引擎后先批量执行上表 `rg` 命令，统一刷新失效项。
