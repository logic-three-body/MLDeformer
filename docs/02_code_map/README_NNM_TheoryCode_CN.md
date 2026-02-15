# NNM（Nearest Neighbor Model）理论-源码映射

## 1. 映射表
| concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation |
|---|---|---|---|---|---|---|---|
| 训练入口 | Retrieval-augmented deform | NearestNeighborModelEditor | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NearestNeighborModel/Source/NearestNeighborModelEditor/Private/NearestNeighborEditorModel.cpp` | `FNearestNeighborEditorModel::Train` | train | 训练前执行 `UpdateForTraining` / 可训练性检查，再调用 `TrainModel<UNearestNeighborTrainingModel>` | 训练帧数需大于 basis 数 |
| 训练后处理 | Post-training asset update | NearestNeighborModelEditor | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NearestNeighborModel/Source/NearestNeighborModelEditor/Private/NearestNeighborEditorModel.cpp` | `OnPostTraining` | train | 成功后失效旧推理缓存并更新文件缓存，再切回推理状态 | 重启编辑器后仍可加载 |
| 训练产物加载 | Optimized network load | NearestNeighborModelEditor | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NearestNeighborModel/Source/NearestNeighborModelEditor/Private/NearestNeighborEditorModel.cpp` | `LoadTrainedNetwork` | train | 加载 `NearestNeighborModel.ubnne` 并初始化实例优化网络 | 文件缺失时应失败并保留错误状态 |
| 输入准备 | Feature assembly and clip | NearestNeighborModel | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NearestNeighborModel/Source/NearestNeighborModel/Private/NearestNeighborModelInstance.cpp` | `SetupInputs` | infer | 构造输入后调用 `ClipInputs`，抑制训练分布外输入 | 异常输入应被裁剪 |
| 推理执行（网络） | Optimized network forward | NearestNeighborModel | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NearestNeighborModel/Source/NearestNeighborModel/Private/NearestNeighborModelInstance.cpp` | `Execute` | infer | 运行优化网络实例 | 统计周期内应有稳定执行时长 |
| 推理执行（完整） | NN + neighbor blending | NearestNeighborModel | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NearestNeighborModel/Source/NearestNeighborModel/Private/NearestNeighborModelInstance.cpp` | `Tick` (`Execute` + `RunNearestNeighborModel`) | infer | 在基础执行后进行邻域细节融合 | 高频细节应优于仅网络分支 |

## 2. NNM 与 NMM 的关键差异
- NMM：以权重回归为主，路径更直接。
- NNM：增加检索与融合阶段，表达更强但状态管理更复杂。

## 3. 训练约束与建议
1. 训练帧数必须高于 basis 数，否则直接失败。
2. 优先保证训练样本覆盖，再调检索细节参数。
3. 训练后务必验证文件缓存与运行时加载路径。

## 4. 最小验证
1. 训练结束后检查 `ubnne` 文件和模型状态。
2. Runtime 对比启停 NNM 的视觉细节差异。
3. 对异常输入姿态验证 `ClipInputs` 是否生效。
