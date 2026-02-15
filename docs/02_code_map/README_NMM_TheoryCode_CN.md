# NMM（Neural Morph Model）理论-源码映射

## 1. 映射表
| concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation |
|---|---|---|---|---|---|---|---|
| 模型训练入口 | Morph weight learning | NeuralMorphModelEditor | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NeuralMorphModel/Source/NeuralMorphModelEditor/Private/NeuralMorphEditorModel.cpp` | `FNeuralMorphEditorModel::Train` | train | 调用 `TrainModel<UNeuralMorphTrainingModel>` 进入训练桥接 | 训练完成后应返回 `ETrainingResult::Success` |
| 训练设备更新 | Device selection | NeuralMorphModelEditor | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NeuralMorphModel/Source/NeuralMorphModelEditor/Private/NeuralMorphEditorModel.cpp` | `UpdateTrainingDeviceList` | train | 刷新可用 CPU/CUDA 设备用于训练侧配置 | 设备列表应与本机环境一致 |
| 训练产物加载 | Trained model loading | NeuralMorphModelEditor | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NeuralMorphModel/Source/NeuralMorphModelEditor/Private/NeuralMorphEditorModel.cpp` | `LoadTrainedNetwork` | train | 从 `onnx` 路径派生 `nmn` 并加载为 `UNeuralMorphNetwork` | 文件不存在时应有错误日志且不污染模型 |
| 输入合法性检查 | Input dimension check | NeuralMorphModel | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NeuralMorphModel/Source/NeuralMorphModel/Private/NeuralMorphModelInstance.cpp` | `SetupInputs` | infer | 检查网络、SkeletalMesh、兼容性、输入维度后再写输入 | 输入维度不一致时应中断执行 |
| 网络推理执行 | Runtime forward | NeuralMorphModel | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NeuralMorphModel/Source/NeuralMorphModel/Private/NeuralMorphModelInstance.cpp` | `Execute` | infer | `NetworkInstance->Run()` 并回填权重到 ExternalMorphSet | `STAT_MLDeformerInference` 应有稳定值 |
| 权重安全机制 | Out-of-distribution guard | NeuralMorphModel | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NeuralMorphModel/Source/NeuralMorphModel/Private/NeuralMorphModelInstance.cpp` | `ClampMorphTargetWeights` 调用路径 | infer | 对网络输出权重进行训练区间 clamp 防止爆炸 | 极端姿态下观察是否仍可控 |

## 2. 训练到推理的数据流
1. Editor 执行 `Train()`。
2. `TrainModel<T>` 调用训练模型并得到返回码。
3. 训练完成后加载网络产物（`nmn`）。
4. Runtime 每帧在 `SetupInputs -> Execute` 路径执行。
5. 输出映射到 Morph 权重，并受 clamp 约束。

## 3. 常见失败模式
- `FailPythonError`：训练桥接类未正确注册或训练脚本异常。
- 输入维度不一致：模型输入配置与网络不匹配。
- 网络文件加载失败：产物缺失、路径错误或版本不兼容。

## 4. 最小验证
1. 训练后确认网络资产已加载且可保存。
2. 运行时确认角色 Morph 权重随动画变化。
3. 打开 `stat MLDeformer`，验证推理时间与预期一致。
