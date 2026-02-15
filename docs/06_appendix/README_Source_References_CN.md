# 源码与资料索引（UE5.5）

## 1. 本项目关键路径
- 项目文件：`MLDeformerSample.uproject`
- 示例 C++ 逻辑：`Source/MLDeformerSample/Public/MLDeformerSampleGameModeBase.h`
- 示例 C++ 逻辑：`Source/MLDeformerSample/Private/MLDeformerSampleGameModeBase.cpp`

## 2. ML Deformer 训练主链（Editor）
- `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFrameworkEditor/Private/MLDeformerEditorToolkit.cpp`
  - `FMLDeformerEditorToolkit::Train`
- `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFrameworkEditor/Public/MLDeformerEditorModel.h`
  - `TrainModel<TrainingModelClass>`
- `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NeuralMorphModel/Source/NeuralMorphModelEditor/Private/NeuralMorphEditorModel.cpp`
  - `FNeuralMorphEditorModel::Train`, `LoadTrainedNetwork`
- `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NearestNeighborModel/Source/NearestNeighborModelEditor/Private/NearestNeighborEditorModel.cpp`
  - `FNearestNeighborEditorModel::Train`, `OnPostTraining`, `LoadTrainedNetwork`

## 3. ML Deformer 推理主链（Runtime）
- `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFramework/Private/MLDeformerComponent.cpp`
  - `UMLDeformerComponent::TickComponent`
- `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFramework/Private/MLDeformerModelInstance.cpp`
  - `UMLDeformerModelInstance::Tick`, `SetNeuralNetworkInputValues`
- `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NeuralMorphModel/Source/NeuralMorphModel/Private/NeuralMorphModelInstance.cpp`
  - `SetupInputs`, `Execute`
- `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NearestNeighborModel/Source/NearestNeighborModel/Private/NearestNeighborModelInstance.cpp`
  - `SetupInputs`, `Execute`, `Tick`

## 4. Groom Deformer 主链
- `D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Source/HairStrandsDeformer/Private/DeformerGroomComponentSource.cpp`
  - `ControlPoint/Curve` 执行域
- `D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Source/HairStrandsDeformer/Private/DeformerDataInterfaceGroom.cpp`
  - 读取接口定义
- `D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Source/HairStrandsDeformer/Private/DeformerDataInterfaceGroomWrite.cpp`
  - 写回接口定义
- `D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Source/HairStrandsCore/Private/GroomDeformerBuilder.cpp`
  - `BuildSkeletalMesh`, `CreateSkeletalMesh`

## 5. 理论文档来源
- 主文档 PDF：`docs/ML Deformer 与 Groom 深度研究.pdf`
- 参考文档总览：`docs/references/docs/README.md`
- 论文导读：`docs/references/docs/paper/README.md`
- 论文代码映射参考：`docs/references/docs/paper_code/README.md`

## 6. 版本约定
- 本索引面向当前本机 `UE 5.5` 源码目录。
- 升级引擎版本时，优先更新本文件中的路径与符号差异。
