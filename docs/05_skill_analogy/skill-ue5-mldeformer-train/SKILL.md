---
name: ue5-mldeformer-train
description: Train and validate UE5 ML Deformer models (Neural Morph / Nearest Neighbor) from editor setup to runtime verification and profiling. Use when you need a repeatable UE5 training + inference + acceptance workflow.
---

# UE5 MLDeformer Train Skill

## trigger
- 用户要求训练或复训 ML Deformer。
- 用户要求从训练产物到运行时推理做闭环验证。
- 用户要求定位训练成功但推理异常的问题。

## prerequisites
- UE5 工程可打开，`MLDeformerFramework` 插件可用。
- 训练输入动画/缓存资源完整。
- 目标 Skeletal Mesh 与训练输入一致。

## steps
1. 执行训练前检查：输入资源、帧数、兼容性、模型参数。
2. 在编辑器触发 Train，记录训练开始时间与返回码。
3. 检查模型产物是否成功加载（NMM `nmn`，NNM `ubnne`）。
4. 进入运行时场景，验证 `TickComponent -> ModelInstance::Tick -> Execute` 是否生效。
5. 记录 `STAT_MLDeformerInference`、运行内存、GPU 内存。
6. 用训练姿态、未见姿态、极限姿态做三组验证。

## outputs
- 训练是否成功（返回码 + 关键日志）。
- 推理是否成功（视觉 + 指标）。
- 问题清单与可执行修复建议。

## failure_modes
- `FailPythonError`：训练桥接或脚本异常。
- 输入维度不一致：训练输入配置与网络结构不匹配。
- 产物加载失败：文件不存在或格式不匹配。
- 推理被短路：权重近零、兼容性失败、输入准备失败。

## verification
- 训练后产物文件存在且可加载。
- 运行时可观察到形变随动画变化。
- `STAT_MLDeformerInference` 有稳定可重复统计值。
- 极端姿态下不出现明显爆炸。
