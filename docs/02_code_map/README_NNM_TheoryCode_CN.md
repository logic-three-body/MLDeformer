# NNM（Nearest Neighbor Model）理论-源码深度映射

> 对应分层文档：
> - `docs/02_code_map/deep_dive/README_L2_Editor_Train_CN.md`
> - `docs/02_code_map/deep_dive/README_L3_Runtime_Infer_CN.md`
> - `docs/02_code_map/deep_dive/README_L7_Shader_RDG_Profiling_CN.md`

## 1. Top-Down 主链（NNM）
1. Editor：`FNearestNeighborEditorModel::Train`。
2. 训练后处理：`FNearestNeighborEditorModel::OnPostTraining`。
3. 产物加载：`FNearestNeighborEditorModel::LoadTrainedNetwork`。
4. Runtime：`UMLDeformerComponent::TickComponent` -> `UMLDeformerModelInstance::Tick`。
5. NNM 分支：`UNearestNeighborModelInstance::SetupInputs` -> `Execute` -> `RunNearestNeighborModel`。

## 2. 训练链映射
| concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation |
|---|---|---|---|---|---|---|---|
| NNM 训练入口 | Retrieval-augmented training | NearestNeighborModelEditor | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NearestNeighborModel/Source/NearestNeighborModelEditor/Private/NearestNeighborEditorModel.cpp` | `FNearestNeighborEditorModel::Train` | train | 调用 `UpdateForTraining` 等检查后进入训练桥 | 样本不足时应失败 |
| 训练桥接 | Generic training abstraction | MLDeformerFrameworkEditor | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFrameworkEditor/Public/MLDeformerEditorModel.h` | `TrainModel<UNearestNeighborTrainingModel>` | train | 复用统一训练模板 | 模型不可训练时返回失败码 |
| 训练后处理 | Cache/state post-processing | NearestNeighborModelEditor | `.../NearestNeighborEditorModel.cpp` | `FNearestNeighborEditorModel::OnPostTraining` | train | 失效旧缓存，切换推理状态，刷新文件缓存 | 训练后缓存时间戳应更新 |
| 训练产物加载 | Optimized network load | NearestNeighborModelEditor | 同上 | `FNearestNeighborEditorModel::LoadTrainedNetwork` | train | 加载 `NearestNeighborModel.ubnne` | 文件缺失应报错 |

## 3. 推理链映射
| concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation |
|---|---|---|---|---|---|---|---|
| 输入装配 | Feature setup and clipping | NearestNeighborModel | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NearestNeighborModel/Source/NearestNeighborModel/Private/NearestNeighborModelInstance.cpp` | `UNearestNeighborModelInstance::SetupInputs` | infer | 组装特征后做输入裁剪，降低 OOD 风险 | 极端输入被裁剪 |
| 优化网络执行 | Optimized network run | NearestNeighborModel | 同上 | `UNearestNeighborModelInstance::Execute` | infer | 跑优化网络得到基础输出 | NNM CSV 指标有数据 |
| 完整推理主循环 | Network + neighbor stage | NearestNeighborModel | 同上 | `UNearestNeighborModelInstance::Tick` | infer | 覆盖基类 Tick，组合执行多阶段路径 | 与 NMM 路径差异可观察 |
| 邻域细节融合 | Neighbor detail synthesis | NearestNeighborModel | 同上 | `UNearestNeighborModelInstance::RunNearestNeighborModel` | infer | 将邻域信息融合到最终形变 | 高频细节增强明显 |

## 4. 关键数据结构
| concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation |
|---|---|---|---|---|---|---|---|
| NNM 模型资产 | NN model state | NearestNeighborModel | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/NearestNeighborModel/Source/NearestNeighborModel/Public/NearestNeighborModel.h` | `UNearestNeighborModel` | both | 管理输入输出维度、section、缓存与网络引用 | 训练前后状态可切换 |
| NNM section | Per-section PCA/neighbor config | NearestNeighborModel | 同上 | `UNearestNeighborModelSection` | both | 维护 section 的 PCA basis、邻域配置等 | section 配置影响输出细节 |
| NNM 运行实例 | Runtime NN executor | NearestNeighborModel | `.../NearestNeighborModelInstance.h` | `UNearestNeighborModelInstance` | infer | 连接优化网络与邻域融合逻辑 | 每帧邻域 id 可读取 |

## 5. 分层链路表（NNM）
| layer | parent_symbol | child_symbol | file_path | thread_context | data_carrier | failure_point | probe |
|---|---|---|---|---|---|---|---|
| L2 | `FNearestNeighborEditorModel::Train` | `FNearestNeighborEditorModel::OnPostTraining` | `.../NearestNeighborEditorModel.cpp` | GameThread(Editor) | 训练产物 + 缓存状态 | 后处理未执行导致旧缓存 | 比较训练前后 cache timestamp |
| L2->L3 | `FNearestNeighborEditorModel::LoadTrainedNetwork` | `UNearestNeighborModelInstance::Execute` | `.../NearestNeighborEditorModel.cpp` -> `.../NearestNeighborModelInstance.cpp` | GameThread | ubnne 网络对象 | 网络对象为空 | 手动破坏文件验证失败 |
| L3 | `UNearestNeighborModelInstance::Tick` | `RunNearestNeighborModel` | `.../NearestNeighborModelInstance.cpp` | GameThread | 近邻 id / PCA 数据 | 近邻索引异常 | 打印 `NearestNeighborIds` |
| L3->L7 | `UNearestNeighborModelInstance::Execute` | `CSV_SCOPED_TIMING_STAT(MLDeformer, NearestNeighborExecute)` | `.../NearestNeighborModelInstance.cpp` | GameThread/Profiler | CSV 指标 | 指标缺失 | 导出 CSV 验证 |

## 6. 常见失败模式
1. 训练阶段：`InputDim`/`OutputDim` 为 0，或 section 配置缺失。
2. 加载阶段：`ubnne` 不存在或架构不匹配。
3. 推理阶段：近邻索引、PCA 数据与当前模型设置不一致。

## 7. 最小验证步骤
1. 训练完成后确认 `NearestNeighborModel.ubnne` 可成功加载。
2. 运行时对比启停 NNM，观察高频细节增强是否符合预期。
3. 同时看视觉结果与 `NearestNeighborExecute` CSV 指标，避免只看单一指标。
