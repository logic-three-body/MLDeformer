# Groom Deformer 理论-源码深度映射（Optimus / ComputeFramework / HairStrands）

> 对应分层文档：
> - `docs/02_code_map/deep_dive/README_L5_Optimus_ComputeGraph_CN.md`
> - `docs/02_code_map/deep_dive/README_L6_DataInterface_Groom_CN.md`
> - `docs/02_code_map/deep_dive/README_L7_Shader_RDG_Profiling_CN.md`

## 1. Top-Down 主链（Groom）
1. DeformerGraph 编译：`UOptimusDeformer::Compile`。
2. Deformer 实例化：`UOptimusDeformer::CreateOptimusInstance` -> `UOptimusDeformerInstance::SetupFromDeformer`。
3. 运行时入队：`UOptimusDeformerInstance::EnqueueWork` -> `FComputeGraphInstance::EnqueueWork`。
4. Groom DataInterface：`CreateDataProvider` -> `AllocateResources` -> `GatherDispatchData`。
5. Shader 执行：`DeformerDataInterfaceGroom*.ush` 读写模板。

## 2. 执行域与 DataInterface 映射
| concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation |
|---|---|---|---|---|---|---|---|
| Groom 执行域 | Domain decomposition | HairStrandsDeformer | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Source/HairStrandsDeformer/Private/DeformerGroomComponentSource.cpp` | `UOptimusGroomComponentSource::GetExecutionDomains` | infer | 定义 `ControlPoint` / `Curve` 两类执行域 | 域计数与数据规模一致 |
| 默认调用数 | Invocation count | HairStrandsDeformer | 同上 | `GetDefaultNumInvocations` | infer | 推导每域 dispatch 数 | 切换域后调用数变化正确 |
| 元素计数 | Domain element count | HairStrandsDeformer | 同上 | `GetComponentElementCountsForExecutionDomain` | infer | unified dispatch 的元素基数 | 元素错配会越界 |
| Groom 读接口 | Read data interface | HairStrandsDeformer | `.../DeformerDataInterfaceGroom.cpp` | `UOptimusGroomDataInterface` | infer | 暴露位置/半径/属性读取函数 | 读取值与资产一致 |
| Groom Guide 接口 | Guide data interface | HairStrandsDeformer | `.../DeformerDataInterfaceGroomGuide.cpp` | `UOptimusGroomGuideDataInterface` | infer | 暴露 guide 相关输入 | guide 映射一致 |
| Groom Exec 接口 | Exec data interface | HairStrandsDeformer | `.../DeformerDataInterfaceGroomExec.cpp` | `UOptimusGroomExecDataInterface` | infer | 暴露执行域相关输入 | dispatch 线程数正确 |
| Groom 写接口 | Write data interface | HairStrandsDeformer | `.../DeformerDataInterfaceGroomWrite.cpp` | `UOptimusGroomWriteDataInterface` | infer | 暴露写回输出（位置/半径/属性） | 写回后可见几何变化 |

## 3. Compute 调度与 Shader 映射
| concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation |
|---|---|---|---|---|---|---|---|
| 图实例入队 | Compute enqueue | ComputeFramework | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/ComputeFramework/Source/ComputeFramework/Private/ComputeGraphInstance.cpp` | `FComputeGraphInstance::EnqueueWork` | infer | 提交 RenderProxy 列表给 worker | proxy 为空时 fallback |
| 参数分发 | Dispatch data gather | ComputeFramework | `.../ComputeGraphWorker.cpp` | `GatherDispatchData` 调用链 | infer | 调用各 provider 的参数写入函数 | 参数 stride 错会直接异常 |
| Shader 读模板 | Read HLSL template | HairStrands | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Shaders/Private/DeformerDataInterfaceGroom.ush` | `Read*` | infer | 读取 groom 控制点和属性 | GPU 捕获确认读值 |
| Shader 写模板 | Write HLSL template | HairStrands | `.../DeformerDataInterfaceGroomWrite.ush` | `Write*` | infer | 写回变形结果到输出缓冲 | 写回后渲染更新 |

## 4. 资产构建链路映射
| concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation |
|---|---|---|---|---|---|---|---|
| Groom 变形骨架生成 | Groom-to-skeletal asset build | HairStrandsCore | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Source/HairStrandsCore/Private/GroomDeformerBuilder.cpp` | `FGroomDeformerBuilder::CreateSkeletalMesh` | asset build | 将 Groom 数据转换为可驱动骨架资产 | skeletal mesh 生成成功 |

## 5. 分层链路表（Groom）
| layer | parent_symbol | child_symbol | file_path | thread_context | data_carrier | failure_point | probe |
|---|---|---|---|---|---|---|---|
| L5->L6 | `UOptimusDeformerInstance::EnqueueWork` | `UOptimusGroomDataInterface::CreateDataProvider` | `.../OptimusDeformerInstance.cpp` -> `.../DeformerDataInterfaceGroom.cpp` | GameThread -> RenderThread | 组件绑定 + provider 对象 | 绑定组件为空 | 命中 `IsValid` 失败分支 |
| L6 | `CreateDataProvider` | `FOptimusGroom*DataProviderProxy::AllocateResources` | `.../DeformerDataInterfaceGroom*.cpp` | RenderThread | SRV/UAV 资源 | 缓冲未分配 | 断点检查 RDG 资源对象 |
| L6->L7 | `FOptimusGroomWriteDataProviderProxy::GatherDispatchData` | `DeformerDataInterfaceGroomWrite.ush` `Write*` | `.../DeformerDataInterfaceGroomWrite.cpp` + `.ush` | RenderThread | 参数缓冲 + UAV | 输出流偏移错误 | 同帧前后缓冲对比 |
| L7 | `FComputeGraphInstance::EnqueueWork` | `ComputeGraphWorker` dispatch | `.../ComputeGraphInstance.cpp` -> `.../ComputeGraphWorker.cpp` | RenderThread | DispatchData | 参数结构尺寸不匹配 | 核查 `ParameterStructSize` |

## 6. 常见失败模式
1. 域配置错误：`ControlPoint` / `Curve` 选择与 kernel 预期不一致。
2. DataProvider 绑定为空：GroomComponent 丢失或绑定类型不匹配。
3. 写回失败：输出掩码或 UAV 绑定错误，导致视觉无变化或闪烁。

## 7. 最小验证步骤
1. 构建最小 DeformerGraph：读取 ControlPoint 并写回固定偏移。
2. 断点 `AllocateResources` / `GatherDispatchData`，确认参数与缓冲正常。
3. GPU 捕获检查 `DeformerDataInterfaceGroomWrite.ush` 写回路径。
