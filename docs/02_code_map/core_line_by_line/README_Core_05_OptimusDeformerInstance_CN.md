# Core-05: `OptimusDeformerInstance.cpp` 逐行解析

## 1. 文件定位
- `D:/UE/UnrealEngine/Engine/Plugins/Animation/DeformerGraph/Source/OptimusCore/Private/OptimusDeformerInstance.cpp`

## 2. 关键行段解析（实例装配）
| line_range | code_focus | explanation | breakpoint_probe |
|---|---|---|---|
| 349-355 | `SetupFromDeformer` 开场 | 记录旧输出缓冲，先 `ReleaseResources()`，支持热重编译。 | 重编译后断点确认资源先释放 |
| 356-367 | 组件绑定刷新 | 用 `InstanceSettings` 解析绑定组件；无设置时临时构造 settings。 | 断点查看 `BoundComponents` 数量 |
| 374-379 | 组件源缓存 | 缓存 `ComponentSource`，供后续 DataInterface 查询。 | 断点验证绑定顺序 |
| 381-387 | 持久缓冲池与值映射 | 初始化 `BufferPool`，拷贝 `ValueMap` 与 override map。 | 验证变量覆盖可见 |
| 388-390 | 执行图与调度队列重置 | 清空 `ComputeGraphExecInfos` 和 `GraphsToRunOnNextTick`。 | 热更新后确保旧图不残留 |
| 392-403 | 构建每个图执行信息 | 复制 graph name/type/compute graph，设置 sort priority。 | 查看 graph index 与优先级 |
| 404-419 | DataProvider 创建 | 优先用绑定组件；失败时回退使用 MeshComponent。 | 人为移除绑定验证 fallback |
| 422-434 | Provider 扩展接口注入 | 给持久缓冲 provider 注入 pool，给 accessor 注入当前 instance。 | 断点检查接口 cast 结果 |
| 437-441 | Setup 图入队 | `Setup` 类型图放入下个 tick 执行集合。 | 首帧观察 setup 图执行 |
| 445-455 | 输出缓冲变更通知 | 输出缓冲变化时 `MarkRenderStateDirty`。 | 调整图输出后观察重建 |

## 3. 关键行段解析（工作入队）
| line_range | code_focus | explanation | breakpoint_probe |
|---|---|---|---|
| 508-524 | 执行组转换 | `ExecutionGroup` 枚举映射到 ComputeFramework 执行组名。 | 验证 Immediate/EndOfFrame 路径 |
| 532-540 | 图资源就绪检查 | 任一图 shader 仍在编译则暂停入队。 | 热编译时验证阻塞行为 |
| 544-549 | 下帧图集合交换 | 用锁交换 `GraphsToRunOnNextTick` 到本地集合。 | 多线程下检查集合一致性 |
| 551-556 | 图遍历入队 | Update 图始终入队，Setup 图按集合入队。 | 断点观察 `GraphsToRun.Contains` |
| 561-569 | 失败 fallback | 入队失败时在渲染线程执行 fallback delegate。 | 人为让 provider 无效触发 |
| 570-574 | Immediate 刷新 | Immediate 成功入队后立刻 `FlushWork`。 | 验证同步执行路径 |

## 4. 控制流总结
1. `SetupFromDeformer` 负责“图和 provider 的静态装配”。
2. `EnqueueWork` 负责“每帧调度与失败降级”。
3. 该文件是 Optimus 层与 ComputeFramework 层的关键桥接点。

## 5. 调试建议
1. 优先看 404-419 是否正确创建 DataProvider。
2. 再看 532-540 是否因 shader 未编译导致不入队。
3. 最后看 561-569 是否一直落入 fallback。
