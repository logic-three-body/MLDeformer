# L3 Runtime 推理链（Runtime Infer）

## 1. 推理主链
1. `UMLDeformerComponent::TickComponent`：组件每帧入口。
2. `UMLDeformerModelInstance::Tick`：统一状态机（权重、兼容性、输入可用性）。
3. 模型分支执行：
   - NMM：`UNeuralMorphModelInstance::SetupInputs` -> `Execute`
   - NNM：`UNearestNeighborModelInstance::SetupInputs` -> `Execute` -> `RunNearestNeighborModel`
4. 后处理：`PostTick`（例如 Morph 模型写回后的统一收敛）。

## 2. 关键源码映射
| concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation |
|---|---|---|---|---|---|---|---|
| 推理总入口 | Online inference loop | MLDeformerFramework | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFramework/Private/MLDeformerComponent.cpp` | `UMLDeformerComponent::TickComponent` | infer | 每帧调用模型实例并统计 `STAT_MLDeformerInference` | `stat MLDeformer` 能看到采样 |
| 统一状态机 | Per-frame inference state machine | MLDeformerFramework | `.../MLDeformerModelInstance.cpp` | `UMLDeformerModelInstance::Tick` | infer | 只在 `ModelWeight>0` 且 `SetupInputs()` 成功时执行 | 把权重设 0 验证回退逻辑 |
| NMM 输入装配 | Feature setup | NeuralMorphModel | `.../NeuralMorphModelInstance.cpp` | `UNeuralMorphModelInstance::SetupInputs` | infer | 校验网络与输入维度，写入输入张量 | 输入维度错配应中断 |
| NMM 前向执行 | Neural forward + morph writeback | NeuralMorphModel | 同上 | `UNeuralMorphModelInstance::Execute` | infer | 调 `NetworkInstance->Run()` 并回填 Morph 权重 | 极端姿态仍需稳定 |
| NNM 输入装配 | Feature setup + clipping | NearestNeighborModel | `.../NearestNeighborModelInstance.cpp` | `UNearestNeighborModelInstance::SetupInputs` | infer | 组装输入并进行裁剪 | OOD 输入应被限制 |
| NNM 主循环 | Model tick override | NearestNeighborModel | 同上 | `UNearestNeighborModelInstance::Tick` | infer | 在基础执行外增加邻域模型路径 | 与仅网络分支对比差异 |
| NNM 邻域执行 | Neighbor detail synthesis | NearestNeighborModel | 同上 | `UNearestNeighborModelInstance::RunNearestNeighborModel` | infer | 融合邻域姿态细节，增强高频形变 | 细节表现提升可观测 |

## 3. 分层链路表（L3）
| layer | parent_symbol | child_symbol | file_path | thread_context | data_carrier | failure_point | probe |
|---|---|---|---|---|---|---|---|
| L3 | `UMLDeformerComponent::TickComponent` | `UMLDeformerModelInstance::Tick` | `.../MLDeformerComponent.cpp` -> `.../MLDeformerModelInstance.cpp` | GameThread | ModelWeight、Pose/Curve 输入 | 组件未初始化或模型实例为空 | 断点看 `ModelInstance` 生命周期 |
| L3 | `UMLDeformerModelInstance::Tick` | `SetupInputs` | `.../MLDeformerModelInstance.cpp` | GameThread | 骨骼矩阵、曲线值、输入缓冲 | 输入数量与网络维度不一致 | 强制改输入配置触发失败 |
| L3 | `UNeuralMorphModelInstance::Execute` | `NetworkInstance->Run()` | `.../NeuralMorphModelInstance.cpp` | GameThread/CPU inference | NNE CPU 模型实例 | 网络实例为空 | 在网络缺失资产下验证保护 |
| L3 | `UNearestNeighborModelInstance::Tick` | `RunNearestNeighborModel` | `.../NearestNeighborModelInstance.cpp` | GameThread | 近邻索引、PCA/偏移数据 | 缓存失效或索引越界 | 打印邻域 id 验证范围 |

## 4. 推理阶段调试优先级
1. 先查是否进入 `UMLDeformerModelInstance::Tick` 执行分支。
2. 再查 `SetupInputs` 是否返回 true。
3. 最后查模型专属 `Execute`/`RunNearestNeighborModel` 是否成功写回。

## 5. 可验证探针
1. `STAT_MLDeformerInference`：验证每帧推理是否执行。
2. `TRACE_CPUPROFILER_EVENT_SCOPE(UMLDeformerComponent::TickComponent)`：定位总开销。
3. `TRACE_CPUPROFILER_EVENT_SCOPE(UNeuralMorphModelInstance::Execute)`：定位 NMM 子开销。
4. `CSV_SCOPED_TIMING_STAT(MLDeformer, NearestNeighborExecute)`：定位 NNM 分支开销。
