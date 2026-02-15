# UE5 ML Deformer 训练与推理实操指南（NMM / NNM / Groom）

## 1. 训练前检查

### 1.1 资产与兼容性
- 验证 Deformer 资产训练输入与当前 Skeletal Mesh 匹配。
- 验证训练动画/几何缓存有效且帧数足够。
- NNM 额外检查：训练帧数 `>` basis 数量。

### 1.2 模型与输入配置
- 输入骨骼列表、曲线列表与训练时定义一致。
- 检查输入维度是否与网络期望一致。
- 确认是否启用权重 clamp 与输入 clip。

## 2. 训练执行链（Editor）
1. `FMLDeformerEditorToolkit::Train` 触发训练。
2. `ActiveModel->OnPreTraining()` 做训练前准备。
3. `ActiveModel->Train()` 进入模型实现。
4. `TrainModel<T>` 调用训练模型的 `Train()`。
5. `OnPostTraining` 处理产物加载、缓存刷新与组件刷新。

## 3. 训练后加载要点
- NMM：`LoadTrainedNetwork` 读取 `nmn`。
- NNM：`LoadTrainedNetwork` 读取 `NearestNeighborModel.ubnne`。
- 失败时应保持旧状态可回退，不覆盖已知可用模型。

## 4. Runtime 推理链
1. `UMLDeformerComponent::TickComponent`
2. `UMLDeformerModelInstance::Tick`
3. `SetupInputs`（维度/兼容性检查）
4. `Execute`（模型推理）
5. 模型特定后处理（权重写回/近邻融合）

## 5. NMM / NNM / Groom 实操重点

### 5.1 NMM
- 关注 Morph 权重写回是否稳定。
- 必要时启用权重 clamp 防止异常姿态放大。

### 5.2 NNM
- 先验证优化网络输出，再验证近邻融合质量。
- 输入 clip 是防止分布外发散的重要防线。

### 5.3 Groom
- 优先验证 ControlPoint 执行域与线程数量。
- 验证 DataInterface 的读写字段是否与图节点一致。

## 6. 常见失败路径
- `FailPythonError`：训练桥接类/脚本异常。
- 训练产物加载失败：文件路径、格式或版本问题。
- 推理不执行：权重接近 0、兼容性失败、输入未准备好。

## 7. 最小验收流程
1. 完成一次训练并确认产物成功加载。
2. 运行角色动画，观察形变稳定性。
3. 打开统计确认推理时间可观测且在预算范围。
4. 切换极限姿态验证无明显爆炸。
