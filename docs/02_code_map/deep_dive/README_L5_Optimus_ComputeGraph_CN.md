# L5 Optimus / ComputeGraph 调度层

## 1. 目标
解释 DeformerGraph 如何从资产编译成可执行 ComputeGraph，并在运行时通过 ComputeFramework 分发。

## 2. 关键源码映射
| concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation |
|---|---|---|---|---|---|---|---|
| Deformer 编译入口 | Graph compilation | OptimusCore | `D:/UE/UnrealEngine/Engine/Plugins/Animation/DeformerGraph/Source/OptimusCore/Private/OptimusDeformer.cpp` | `UOptimusDeformer::Compile` | infer | 把节点图编译为 `UComputeGraph` 与执行信息 | 编译失败时 Diagnostic 应可见 |
| 节点图编译 | Node graph to compute graph | OptimusCore | 同上 | `UOptimusDeformer::CompileNodeGraphToComputeGraphs` | infer | 将图节点/数据接口解析为 kernel 与连接拓扑 | 编译结果含 graph 数与期望一致 |
| 实例创建 | Runtime instance build | OptimusCore | 同上 | `UOptimusDeformer::CreateOptimusInstance` | infer | 为 mesh 组件创建 `UOptimusDeformerInstance` 并绑定回调 | 重新编译后实例能重新 setup |
| 实例装配 | Instance setup from deformer | OptimusCore | `.../OptimusDeformerInstance.cpp` | `UOptimusDeformerInstance::SetupFromDeformer` | infer | 绑定组件、创建 data provider、准备执行图列表 | 绑定缺失时应退化或报错 |
| 实例入队 | Enqueue compute work | OptimusCore | 同上 | `UOptimusDeformerInstance::EnqueueWork` | infer | 遍历执行图并调用 `ComputeGraphInstance.EnqueueWork` | 图为空时 fallback 执行 |
| ComputeGraph 实例入队 | Dispatch bridge | ComputeFramework | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/ComputeFramework/Source/ComputeFramework/Private/ComputeGraphInstance.cpp` | `FComputeGraphInstance::EnqueueWork` | infer | 将 DataProvider RenderProxy 打包并提交 worker | DataProvider 校验失败时拒绝执行 |
| Compute worker 分发 | Render-side dispatch | ComputeFramework | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/ComputeFramework/Source/ComputeFramework/Private/ComputeGraphWorker.cpp` | `GatherDispatchData` 调用链 | infer | 统一调用各 DataProvider 的 `AllocateResources` / `GatherDispatchData` | 参数布局错误会直接污染 kernel 输入 |

## 3. 分层链路表（L5）
| layer | parent_symbol | child_symbol | file_path | thread_context | data_carrier | failure_point | probe |
|---|---|---|---|---|---|---|---|
| L5 | `UOptimusDeformer::Compile` | `CompileNodeGraphToComputeGraphs` | `.../OptimusDeformer.cpp` | GameThread(Editor/Load) | Graph IR / diagnostics | 节点验证失败 | 捕获 `CompileMessageDelegate` |
| L5 | `UOptimusDeformer::CreateOptimusInstance` | `UOptimusDeformerInstance::SetupFromDeformer` | `.../OptimusDeformer.cpp` + `.../OptimusDeformerInstance.cpp` | GameThread | Component bindings | 组件绑定不完整 | 断点检查 `BoundComponents` |
| L5 | `UOptimusDeformerInstance::EnqueueWork` | `FComputeGraphInstance::EnqueueWork` | `.../OptimusDeformerInstance.cpp` + `.../ComputeGraphInstance.cpp` | GameThread -> RenderThread | DataProviders + ExecutionGroupName | provider render proxy 为空 | 强制无效 binding 验证 fallback |
| L5 | `FComputeGraphInstance::EnqueueWork` | `ComputeGraphWorker` 的 `GatherDispatchData` | `.../ComputeGraphInstance.cpp` + `.../ComputeGraphWorker.cpp` | RenderThread | ParameterBuffer / DispatchData | 参数 stride 与 struct 不一致 | 检查 `ParameterStructSize` |

## 4. 与 Groom 的耦合点
1. Groom 的 `UOptimusGroom*DataInterface` 最终都走 `CreateDataProvider` -> `FComputeDataProviderRenderProxy`。
2. 因此 Groom Debug 的核心通常不在图节点，而在 DataProvider 参数装配是否正确。

## 5. 可验证探针
1. 在 `UOptimusDeformer::Compile` 断点，核对 `Status` 从 `Compiling` 到 `Compiled`。
2. 在 `UOptimusDeformerInstance::EnqueueWork` 断点，核对 `GraphsToRunOnNextTick` 非空。
3. 在 `FComputeGraphInstance::EnqueueWork` 断点，核对每个 DataProvider 都能生成 RenderProxy。
4. 在 `ComputeGraphWorker.cpp` 观察 `GatherDispatchData` 是否按 kernel index 正确写参数。
