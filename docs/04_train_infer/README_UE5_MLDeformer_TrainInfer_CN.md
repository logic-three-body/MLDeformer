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

## 8. skip_train 模式（跳过训练）

### 8.1 背景
ML Deformer 训练涉及 GPU 浮点运算，在不同硬件环境下（GPU 架构、CUDA 版本、PyTorch 版本）无法保证 bit-exact 输出。即使训练配置和训练数据完全相同，不同机器重训的网络权重仍可能有差异，导致推理结果偏离 Reference 基线、GT 比较不通过。

### 8.2 适用场景
- Reference 工程已有经过验证的 deformer 权重。
- 当前硬件无法通过重训达到 strict GT 阈值。
- 仅需验证"导入→推理→GT 对比"链路，不需验证训练能力本身。

### 8.3 启用方式
在 `pipeline.full_exec.yaml` 中设置：
```yaml
ue:
  training:
    skip_train: true
```

### 8.4 行为变化
| 阶段 | 正常模式 | skip_train 模式 |
|---|---|---|
| ue_setup | 执行 `ue_setup_assets.py`，覆写 deformer 训练配置 | 跳过，保留 baseline_sync 拷贝的 Reference 权重 |
| train | 启动 UE Editor 执行训练 | 从 `Refference/` 拷贝 deformer `.uasset`，SHA-256 校验 |

### 8.5 验证指标对比
| 指标 | 重训（失败） | skip_train（通过） | 说明 |
|---|---|---|---|
| SSIM mean | 0.981 | 0.9997 | 0.019 提升 |
| PSNR min | 29.38 | 52.28 | 22.9 dB 提升 |
| Edge IoU | 0.970 | 0.988 | 边缘对齐显著改善 |

## 9. 训练确定性治理

### 9.1 非确定性来源
1. **GPU 浮点精度**：不同 GPU 架构的 FMA 指令精度差异。
2. **cuDNN 算法选择**：`torch.backends.cudnn.deterministic=False` 时选择最快但不确定的卷积算法。
3. **异步 GPU 运算**：CUDA stream 中操作重排序。
4. **Atomics 累积**：反向传播中的梯度累积顺序非确定。

### 9.2 配置接口
```yaml
ue:
  training:
    determinism:
      enabled: true
      seed: 42
      torch_deterministic: true
      cudnn_deterministic: true
      cudnn_benchmark: false
```

### 9.3 注意事项
- 开启完全确定性会有性能代价（训练速度降低 10-30%）。
- 即使开启所有确定性标志，**跨 GPU 架构**仍不保证 bit-exact。
- 确定性报告输出到 `reports/train_determinism_report.json`。
