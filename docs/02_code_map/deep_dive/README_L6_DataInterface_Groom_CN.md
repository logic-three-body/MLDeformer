# L6 Groom DataInterface 机制

## 1. 目标
解释 Groom 在 DeformerGraph 中如何定义执行域、暴露读写接口、分配资源并向 kernel 提供 dispatch 参数。

## 2. 关键源码映射
| concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation |
|---|---|---|---|---|---|---|---|
| 执行域定义 | Domain decomposition | HairStrandsDeformer | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Source/HairStrandsDeformer/Private/DeformerGroomComponentSource.cpp` | `UOptimusGroomComponentSource::GetExecutionDomains` | infer | 暴露 `ControlPoint` / `Curve` 两个执行域 | 图里域选择与资源维度一致 |
| 默认线程数 | Invocation sizing | HairStrandsDeformer | 同上 | `GetDefaultNumInvocations` | infer | 根据域推导 dispatch 调用数 | 域切换后线程数变化正确 |
| 元素计数 | Domain element counts | HairStrandsDeformer | 同上 | `GetComponentElementCountsForExecutionDomain` | infer | 返回每域元素计数供 unified dispatch 使用 | 错计数会导致越界 |
| Groom 读接口 | Read DI | HairStrandsDeformer | `.../DeformerDataInterfaceGroom.cpp` | `UOptimusGroomDataInterface::GetSupportedInputs` | infer | 暴露位置/半径/属性读取函数 | 读取到的属性与资产一致 |
| Groom Guide 接口 | Guide DI | HairStrandsDeformer | `.../DeformerDataInterfaceGroomGuide.cpp` | `UOptimusGroomGuideDataInterface::GetSupportedInputs` | infer | 暴露 guide 相关映射与读取 | guide 索引映射无错位 |
| Groom Exec 接口 | Exec DI | HairStrandsDeformer | `.../DeformerDataInterfaceGroomExec.cpp` | `UOptimusGroomExecDataInterface::GetSupportedInputs` | infer | 提供域执行辅助输入 | 线程计数与域一致 |
| Groom 写接口 | Write DI | HairStrandsDeformer | `.../DeformerDataInterfaceGroomWrite.cpp` | `UOptimusGroomWriteDataInterface::GetSupportedOutputs` | infer | 暴露写回输出函数（位置/半径/属性） | 写回后渲染结果更新 |
| DataProvider 创建 | Provider bridge | HairStrandsDeformer | `.../DeformerDataInterfaceGroom*.cpp` | `CreateDataProvider` | infer | 组件绑定到具体 RenderProxy | 绑定为空时返回空 provider |
| 资源分配/分发 | RDG parameter preparation | HairStrandsDeformer | `.../DeformerDataInterfaceGroom*.cpp` | `AllocateResources`, `GatherDispatchData` | infer | 组装 SRV/UAV 和参数缓冲给 kernel | 参数写错会导致明显伪影 |

## 3. 分层链路表（L6）
| layer | parent_symbol | child_symbol | file_path | thread_context | data_carrier | failure_point | probe |
|---|---|---|---|---|---|---|---|
| L6 | `UOptimusGroomComponentSource::GetExecutionDomains` | `GetComponentElementCountsForExecutionDomain` | `.../DeformerGroomComponentSource.cpp` | GameThread -> RenderPrep | Domain 名称与元素计数 | 域名不匹配 | 输出 `ControlPoint/Curve` 计数 |
| L6 | `UOptimusGroomDataInterface::CreateDataProvider` | `FOptimusGroomDataProviderProxy::AllocateResources` | `.../DeformerDataInterfaceGroom.cpp` | RenderThread | Groom 资源 SRV/UAV | 绑定组件无效 | 触发 `IsValid` 分支 |
| L6 | `UOptimusGroomGuideDataInterface::CreateDataProvider` | `FOptimusGroomGuideDataProviderProxy::GatherDispatchData` | `.../DeformerDataInterfaceGroomGuide.cpp` | RenderThread | guide 索引缓冲 | guide 缓冲空 | 检查 guide buffer 绑定 |
| L6 | `UOptimusGroomWriteDataInterface::CreateDataProvider` | `FOptimusGroomWriteDataProviderProxy::GatherDispatchData` | `.../DeformerDataInterfaceGroomWrite.cpp` | RenderThread | 输出写回缓冲 | 输出掩码错误 | 写回后曲线位置是否更新 |
| L6 | `UOptimusGroomExecDataInterface::CreateDataProvider` | `FOptimusGroomExecDataProviderProxy::GetDispatchThreadCount` | `.../DeformerDataInterfaceGroomExec.cpp` | RenderThread | 每域线程数 | 线程数/域不一致 | 验证不同域的 thread count |

## 4. 与资产构建链路
- `D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Source/HairStrandsCore/Private/GroomDeformerBuilder.cpp`
  - `FGroomDeformerBuilder::CreateSkeletalMesh`
- 作用：把 Groom 数据转换为可驱动骨架/网格表示，供后续执行链路消费。

## 5. 可验证探针
1. 断点 `UOptimusGroomComponentSource::GetExecutionDomains`，确认域稳定为 `ControlPoint`/`Curve`。
2. 断点 `FOptimusGroomWriteDataProviderProxy::AllocateResources`，确认 UAV/SRV 分配成功。
3. 断点 `FOptimusGroomWriteDataProviderProxy::GatherDispatchData`，确认参数按 invocation 写入。
