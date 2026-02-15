# UE5 MLDeformer 架构图总结（Architecture Diagram）

> 基线：`UE_ROOT = D:/UE/UnrealEngine`，`EngineAssociation = 5.5`

## 1. 总体分层架构图
```mermaid
flowchart TD
    A[Editor Toolkit\nFMLDeformerEditorToolkit::Train] --> B[Editor Model\nTrainModel<T>]
    B --> C[NMM/NNM TrainingModel]
    C --> D[Trained Artifacts\nonnx/nmn/ubnne]

    E[UMLDeformerComponent::TickComponent] --> F[UMLDeformerModelInstance::Tick]
    F --> G[NMM/NNM Execute]
    G --> H[USkinnedMeshComponent\nMeshDeformer Instance]

    H --> I[UOptimusDeformerInstance\nEnqueueWork]
    I --> J[FComputeGraphInstance::EnqueueWork]
    J --> K[ComputeGraphWorker\nAllocate + Gather + Dispatch]

    K --> L[UOptimusGroom*DataInterface]
    L --> M[DeformerDataInterfaceGroom*.ush]
    M --> N[RDG Compute Pass]
    N --> O[Deformed Buffers / Final Render]
```

## 2. 训练链时序图（Editor）
```mermaid
sequenceDiagram
    participant UI as MLDeformer Editor UI
    participant Toolkit as FMLDeformerEditorToolkit
    participant EditorModel as FMLDeformerEditorModel
    participant TrainModel as TrainModel<T>
    participant ModelEditor as NMM/NNM EditorModel

    UI->>Toolkit: Train()
    Toolkit->>EditorModel: Train()
    EditorModel->>TrainModel: TrainModel<T>()
    TrainModel->>ModelEditor: TrainingModel::Train
    ModelEditor-->>Toolkit: ETrainingResult
    Toolkit->>ModelEditor: LoadTrainedNetwork()
    Toolkit->>ModelEditor: OnPostTraining()
```

## 3. 推理链时序图（Runtime）
```mermaid
sequenceDiagram
    participant Comp as UMLDeformerComponent
    participant Inst as UMLDeformerModelInstance
    participant ModelInst as NMM/NNM ModelInstance
    participant Skel as USkinnedMeshComponent

    Comp->>Inst: Tick(DeltaTime, Weight)
    Inst->>ModelInst: SetupInputs()
    Inst->>ModelInst: Execute(Weight)
    ModelInst-->>Inst: Morph/NN outputs
    Inst->>ModelInst: PostTick()
    Skel->>Skel: EnqueueWork(MeshDeformer)
```

## 4. Compute 调度图（Optimus / ComputeFramework）
```mermaid
flowchart LR
    A[UOptimusDeformer::Compile] --> B[UOptimusDeformer::CreateOptimusInstance]
    B --> C[UOptimusDeformerInstance::SetupFromDeformer]
    C --> D[CreateDataProviders]
    D --> E[UOptimusDeformerInstance::EnqueueWork]
    E --> F[FComputeGraphInstance::EnqueueWork]
    F --> G[ComputeGraphWorker]
    G --> H[AllocateResources]
    G --> I[GatherDispatchData]
    G --> J[AddPass Dispatch]
```

## 5. Groom 写回图（DataInterface -> Shader）
```mermaid
flowchart TD
    A[UOptimusGroomWriteDataInterface] --> B[CreateDataProvider]
    B --> C[FOptimusGroomWriteDataProviderProxy]
    C --> D[AllocateResources]
    C --> E[GatherDispatchData]
    D --> F[SRV/UAV Binding]
    E --> G[Parameter Buffer]
    F --> H[DeformerDataInterfaceGroomWrite.ush]
    G --> H
    H --> I[RDG Compute Pass]
    I --> J[Groom Deformed Buffers]
```

## 6. 性能与观测点（架构视角）
1. CPU 推理入口：`STAT_MLDeformerInference`（`UMLDeformerComponent::TickComponent`）。
2. 模型分支：
   - NMM：`CSV_SCOPED_TIMING_STAT(MLDeformer, NeuralMorphExecute)`
   - NNM：`CSV_SCOPED_TIMING_STAT(MLDeformer, NearestNeighborExecute)`
3. Compute 层：`ComputeGraphWorker` 的统一分发与 fallback 路径。
4. Groom 层：`AllocateResources` / `GatherDispatchData` 参数和缓冲绑定一致性。

## 7. 与文档体系的关系
- 分层解析：`docs/02_code_map/deep_dive/`
- 逐行核心解析：`docs/02_code_map/core_line_by_line/README_Core_LineByLine_Index_CN.md`
- 模型专题映射：NMM / NNM / Groom 三篇专题文档
