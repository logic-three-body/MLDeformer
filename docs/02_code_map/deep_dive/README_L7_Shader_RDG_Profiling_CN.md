# L7 Shader / RDG / Profiling

## 1. 目标
把 DataInterface 的 CPU 侧参数装配映射到 Shader 模板与 RDG 执行，并给出可观测指标。

## 2. Shader 模板与 DataInterface 对应
| concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation |
|---|---|---|---|---|---|---|---|
| Groom 读模板 | Read path template | HairStrands (Shaders) | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Shaders/Private/DeformerDataInterfaceGroom.ush` | `Read*` 系列函数 | infer | 从 groom 资源读取位置/属性/映射 | GPU capture 验证读值 |
| Groom Guide 模板 | Guide lookup template | HairStrands (Shaders) | `.../DeformerDataInterfaceGroomGuide.ush` | guide 访问函数 | infer | guide/curve 关系查询 | guide 索引一致性 |
| Groom Exec 模板 | Exec domain template | HairStrands (Shaders) | `.../DeformerDataInterfaceGroomExec.ush` | exec 域辅助函数 | infer | 为域执行提供线程相关输入 | thread id 与域匹配 |
| Groom 写模板 | Write path template | HairStrands (Shaders) | `.../DeformerDataInterfaceGroomWrite.ush` | `Write*` 系列函数 | infer | 写回控制点位置/半径/属性 | 写回后渲染变化 |

## 3. RDG / Dispatch 关键点
| concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation |
|---|---|---|---|---|---|---|---|
| RenderProxy 资源分配 | RDG allocation | HairStrandsDeformer | `.../DeformerDataInterfaceGroom.cpp` | `FOptimusGroomDataProviderProxy::AllocateResources` | infer | 在 RDG 图中准备外部缓冲与视图 | 缓冲为空时应阻断 |
| RenderProxy 参数收集 | Dispatch parameter fill | HairStrandsDeformer | `.../DeformerDataInterfaceGroom.cpp` | `FOptimusGroomDataProviderProxy::GatherDispatchData` | infer | 填充 kernel 参数结构体 | 参数结构大小要匹配 |
| 统一入队桥 | Compute enqueue bridge | ComputeFramework | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/ComputeFramework/Source/ComputeFramework/Private/ComputeGraphInstance.cpp` | `FComputeGraphInstance::EnqueueWork` | infer | 将 RenderProxy 列表提交 worker | proxy 无效触发 fallback |
| Worker 分发 | Dispatch execution | ComputeFramework | `.../ComputeGraphWorker.cpp` | `GatherDispatchData` 调用点 | infer | 按 kernel 索引和 invocation 写参数并发起 dispatch | 参数 stride 错会出错 |

## 4. Profiling 与可观测指标（必须关注）
| 指标/探针 | 路径 | 作用 | 典型用法 |
|---|---|---|---|
| `STAT_MLDeformerInference` | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFramework/Public/MLDeformerModelInstance.h` + `.../Private/MLDeformerModelInstance.cpp` | 统计整体推理耗时 | 运行时 `stat MLDeformer` |
| `SCOPE_CYCLE_COUNTER(STAT_MLDeformerInference)` | `.../MLDeformerComponent.cpp` | 在组件 tick 统计推理段 | 检查每帧是否进入推理 |
| `TRACE_CPUPROFILER_EVENT_SCOPE(UNeuralMorphModelInstance::Execute)` | `.../NeuralMorphModelInstance.cpp` | NMM 子路径 CPU 采样 | 定位 NMM 局部热点 |
| `CSV_SCOPED_TIMING_STAT(MLDeformer, NeuralMorphExecute)` | `.../NeuralMorphModelInstance.cpp` | NMM CSV 指标输出 | 比较不同配置耗时 |
| `CSV_SCOPED_TIMING_STAT(MLDeformer, NearestNeighborExecute)` | `.../NearestNeighborModelInstance.cpp` | NNM CSV 指标输出 | 对比 NMM 与 NNM 成本 |

## 5. 分层链路表（L7）
| layer | parent_symbol | child_symbol | file_path | thread_context | data_carrier | failure_point | probe |
|---|---|---|---|---|---|---|---|
| L7 | `CreateDataProvider` | `GetShaderVirtualPath` / `GetHLSL` | `.../DeformerDataInterfaceGroom*.cpp` | GameThread -> Render compile path | Shader virtual path / generated HLSL | 虚拟路径错误 | 核对 `TemplateFilePath` |
| L7 | `FOptimusGroom*DataProviderProxy::AllocateResources` | `FOptimusGroom*DataProviderProxy::GatherDispatchData` | `.../DeformerDataInterfaceGroom*.cpp` | RenderThread | RDG SRV/UAV + parameter buffer | 参数未写满 | 检查 `ParameterBufferStride` |
| L7 | `FComputeGraphInstance::EnqueueWork` | `ComputeGraphWorker::GatherDispatchData` | `.../ComputeGraphInstance.cpp` -> `.../ComputeGraphWorker.cpp` | RenderThread | DispatchData | provider 校验失败 | 检查 `IsValid()` 返回值 |
| L7 | `UNeuralMorphModelInstance::Execute` | `NetworkInstance->Run` + morph 回填 | `.../NeuralMorphModelInstance.cpp` | GameThread/CPU inference | 输入/输出 tensor + morph 权重 | 输出越界/抖动 | 观察 clamp 后权重稳定性 |

## 6. 可验证探针
1. 执行 `stat MLDeformer`，确认 `STAT_MLDeformerInference` 连续采样。
2. 打开 CPU Trace，验证 `TickComponent` -> `SetupInputs` -> `Execute` 时间链。
3. 在 Groom 写回路径下对同一帧抓取 UAV 前后值，确认 `Write*` 生效。
4. 对 NMM/NNM 导出 CSV，比较 `NeuralMorphExecute` 与 `NearestNeighborExecute`。
