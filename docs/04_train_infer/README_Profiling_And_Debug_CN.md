# 性能与排障指南（ML Deformer / Groom）

## 1. 核心指标

### 1.1 推理时间
- `STAT_MLDeformerInference`
- 路径来源：`UMLDeformerComponent::TickComponent` 中 `SCOPE_CYCLE_COUNTER(STAT_MLDeformerInference)`

### 1.2 内存
- 关注模型运行时内存与 GPU 相关占用。
- 示例工程中可通过 GameMode 暴露的统计函数观察：
  - `GetMLRuntimeMemoryInBytes`
  - `GetMLGPUMemoryInBytes`

## 2. 常见问题与处理

### 2.1 看不到形变
排查顺序：
1. Deformer 资产是否绑定正确。
2. 模型是否训练成功且产物已加载。
3. 模型权重是否接近 0。
4. 输入骨骼/曲线是否可用。

### 2.2 推理时间异常升高
排查顺序：
1. 近期是否切换了更重的模型配置。
2. 是否在同帧叠加了额外 Morph/Deformer 逻辑。
3. 是否存在调试可视化开销（编辑器模式）。

### 2.3 极限姿态爆炸
排查顺序：
1. 训练数据覆盖是否不足。
2. 输入是否超出训练分布。
3. 是否启用输入 clip 与权重 clamp。

### 2.4 Groom 结果闪烁或错位
排查顺序：
1. ControlPoint/Curve 执行域数量是否匹配。
2. DataInterface 写回 buffer 是否有效。
3. 组索引与 binding 是否一致。

## 3. 建议监控节奏
- 训练后：做一次固定动作集基准回放，记录平均推理时间。
- 每次配置变更后：复测同一动作集，避免对比口径漂移。
- 保留版本化性能记录：`model_version / data_version / metrics`。

## 4. 现场排障最小模板
```text
Issue:
EngineVersion:
ModelType:
DataVersion:
ReproSteps:
Expected:
Actual:
StatsSnapshot:
FixAttempt:
Result:
```
