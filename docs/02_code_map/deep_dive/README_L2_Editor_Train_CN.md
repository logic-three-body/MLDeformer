# L2 Editor 训练链（Editor Train）

## 1. 训练主链（顶层到模型）
1. `FMLDeformerEditorToolkit::Train`：UI 触发训练，处理结果分支。
2. `FMLDeformerEditorModel::Train` / `TrainModel<T>`：训练抽象层。
3. 各模型覆盖：
   - NMM：`FNeuralMorphEditorModel::Train`
   - NNM：`FNearestNeighborEditorModel::Train`
4. 训练后加载：`LoadTrainedNetwork`。
5. 训练后收敛与缓存处理：`OnPostTraining`（NNM 重点）。

## 2. 关键源码映射
| concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation |
|---|---|---|---|---|---|---|---|
| 训练入口 | Training orchestration | MLDeformerFrameworkEditor | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFrameworkEditor/Private/MLDeformerEditorToolkit.cpp` | `FMLDeformerEditorToolkit::Train` | train | Train 按钮触发后汇总预检查、执行、结果处理 | 触发训练并确认进入该函数 |
| 结果分支 | Result handling | MLDeformerFrameworkEditor | 同上 | `FMLDeformerEditorToolkit::HandleTrainingResult` | train | 失败、部分成功、成功路径统一收敛 | 人为构造失败验证错误分支 |
| 抽象训练入口 | Base training interface | MLDeformerFrameworkEditor | `.../MLDeformerEditorModel.cpp` | `FMLDeformerEditorModel::Train` | train | 基类默认告警，要求派生类覆盖 | 未覆盖时应有警告日志 |
| 模板训练桥 | Generic training bridge | MLDeformerFrameworkEditor | `.../MLDeformerEditorModel.h` | `TrainModel<TrainingModelClass>` | train | 把训练执行委托给具体 TrainingModel | 训练模型未就绪时返回失败码 |
| NMM 训练 | Neural morph training | NeuralMorphModelEditor | `.../NeuralMorphEditorModel.cpp` | `FNeuralMorphEditorModel::Train` | train | 调用 `TrainModel<UNeuralMorphTrainingModel>` | 训练后 NMM 产物可加载 |
| NMM 加载 | NMM network load | NeuralMorphModelEditor | 同上 | `FNeuralMorphEditorModel::LoadTrainedNetwork` | train | 从训练产物重建可推理网络对象 | 产物缺失时应报错 |
| NNM 训练 | Nearest-neighbor training | NearestNeighborModelEditor | `.../NearestNeighborEditorModel.cpp` | `FNearestNeighborEditorModel::Train` | train | 训练前检查输入输出维度与训练条件 | `UpdateForTraining` 失败可复现 |
| NNM 后处理 | Post training invalidate/update | NearestNeighborModelEditor | 同上 | `FNearestNeighborEditorModel::OnPostTraining` | train | 刷新缓存、失效旧推理状态、切回推理模式 | 训练后重启仍可加载 |
| NNM 加载 | NNM network load | NearestNeighborModelEditor | 同上 | `FNearestNeighborEditorModel::LoadTrainedNetwork` | train | 加载 `NearestNeighborModel.ubnne` | 文件不存在应失败 |

## 3. 分层链路表（L2）
| layer | parent_symbol | child_symbol | file_path | thread_context | data_carrier | failure_point | probe |
|---|---|---|---|---|---|---|---|
| L2 | `FMLDeformerEditorToolkit::Train` | `FMLDeformerEditorModel::Train` | `.../MLDeformerEditorToolkit.cpp` -> `.../MLDeformerEditorModel.cpp` | GameThread(Editor) | 训练配置、训练样本引用 | 基类未覆盖导致空实现 | 观察 Warning: override Train |
| L2 | `FMLDeformerEditorModel::Train` | `TrainModel<T>` | `.../MLDeformerEditorModel.h` | GameThread(Editor) | TrainingModel 实例 | 训练模型创建失败 | 断点确认模板实例化类型 |
| L2 | `TrainModel<UNeuralMorphTrainingModel>` | `FNeuralMorphEditorModel::LoadTrainedNetwork` | `.../NeuralMorphEditorModel.cpp` | GameThread(Editor) | onnx/nmn 文件 | 产物路径错误 | 删除产物文件验证错误日志 |
| L2 | `TrainModel<UNearestNeighborTrainingModel>` | `FNearestNeighborEditorModel::OnPostTraining` | `.../NearestNeighborEditorModel.cpp` | GameThread(Editor) | ubnne 文件 + 缓存时间戳 | 缓存未更新导致旧模型 | 比较训练前后缓存时间戳 |

## 4. 训练阶段高频失败点
1. 训练输入维度和模型设置不一致（骨骼/曲线配置漂移）。
2. 训练产物路径无效（缓存目录、文件命名、权限）。
3. NNM 训练样本不足（帧数、section/basis 配置不满足）。

## 5. 可验证探针
1. 在 `FMLDeformerEditorToolkit::HandleTrainingResult` 断点，验证不同返回码分支。
2. 在 `FNeuralMorphEditorModel::LoadTrainedNetwork` 与 `FNearestNeighborEditorModel::LoadTrainedNetwork` 同时断点，确认模型分支差异。
3. 训练后比较模型缓存时间戳与网络文件写入时间，验证后处理生效。
