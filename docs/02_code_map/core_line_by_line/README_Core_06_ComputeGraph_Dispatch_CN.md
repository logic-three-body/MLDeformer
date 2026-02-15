# Core-06: `ComputeGraphInstance.cpp` + `ComputeGraphWorker.cpp` 逐行解析

## 1. 文件定位
- `D:/UE/UnrealEngine/Engine/Plugins/Runtime/ComputeFramework/Source/ComputeFramework/Private/ComputeGraphInstance.cpp`
- `D:/UE/UnrealEngine/Engine/Plugins/Runtime/ComputeFramework/Source/ComputeFramework/Private/ComputeGraphWorker.cpp`

## 2. `ComputeGraphInstance.cpp` 关键行段
| line_range | code_focus | explanation | breakpoint_probe |
|---|---|---|---|
| 16-21 | `CreateDataProviders` | 由 `UComputeGraph` 根据绑定对象创建 provider 列表。 | 断点验证 provider 数量 |
| 29-39 | 入队前基础条件 | graph/scene 为空或框架禁用时直接失败。 | 人为置空 scene 验证 |
| 41-45 | 绑定校验 | `ValidateProviders(DataProviders)` 失败则拒绝提交。 | 绑定缺失时验证快速失败 |
| 48-52 | worker 获取 | 从 scene 取 `FComputeGraphTaskWorker`，失败即返回。 | 检查场景切换下 worker 是否可用 |
| 54-62 | render proxy 校验 | 若 proxy 空，尝试 `UpdateResources()`（延迟编译）并返回 false。 | 首次加载图时验证该分支 |
| 64-71 | provider proxy 采集 | 把 `UComputeDataProvider` 转成 RenderProxy，保留空槽位对齐索引。 | 断点核对索引稳定性 |
| 73-78 | 渲染线程入队 | `ENQUEUE_RENDER_COMMAND` 把执行请求交给 worker，转移 proxy 所有权。 | 断点检查捕获参数 |
| 80 | 返回成功 | 成功仅表示“请求已入队”，非执行已完成。 | 对照实际执行时机 |

## 3. `ComputeGraphWorker.cpp` 关键行段
| line_range | code_focus | explanation | breakpoint_probe |
|---|---|---|---|
| 121-128 | kernel 提交描述创建 | 为每个 kernel 创建 `SubmitDesc`，记录图/核索引与排序键。 | 验证多图排序行为 |
| 136 | 子调用线程数 | 从执行 provider 读取 `GetDispatchThreadCount(ThreadCounts)`。 | 检查 unified 前线程数 |
| 146-163 | provider 校验与 permutation | 按参数成员遍历 provider，`IsValid` + `GatherPermutations`。 | 参数结构不匹配时应失败 |
| 167-172 | shader 可用性校验 | 对每个子调用取 shader，任一无效则整图不执行。 | 强制触发编译未就绪 |
| 175-187 | unified dispatch 判定 | 若全部子调用 shader 相同，压缩为 unified dispatch。 | 检查性能收益与行为一致 |
| 194-200 | 失败 fallback | 校验失败就回退并执行 fallback delegate。 | 断点确认失败收敛 |
| 203-212 | RDG 资源分配 | 调每个 provider 的 `AllocateResources(GraphBuilder, ...)`。 | 验证资源申请时机 |
| 234-245 | dispatch 线程整理 | unified 时合并 thread count 并降为单调用。 | 断点比对前后线程数 |
| 248-250 | 参数缓冲初始化 | 构造 `FDispatchData`（stride、offset、struct size 等）。 | 观察 `ParameterArray.GetStride()` |
| 255-276 | `GatherDispatchData` | 逐 provider 写参数；非 primary provider 强制 unified 视图。 | 检查 secondary provider 的统一视图 |
| 280-296 | RDG AddPass 提交 | 按子调用提交 compute pass 到 RDG。 | GPU capture 确认 pass 数量 |

## 4. 控制流总结
1. `ComputeGraphInstance` 负责“前置校验 + 跨线程入队”。
2. `ComputeGraphWorker` 负责“校验 + 资源分配 + 参数装填 + RDG dispatch”。
3. 失败路径统一回落到 fallback，保证渲染链不崩。

## 5. 调试建议
1. 若图不执行，先看 `ComputeGraphInstance.cpp:54-62`（proxy 是否存在）。
2. 若执行异常，重点看 `ComputeGraphWorker.cpp:146-163` 和 `248-276`（参数合法性）。
3. 若性能异常，重点看 unified dispatch（175-187）是否被触发。
