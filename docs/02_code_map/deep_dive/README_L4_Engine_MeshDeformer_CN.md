# L4 Engine MeshDeformer 集成层（USkinnedMeshComponent / GPUSkin）

## 1. 目标
把 MLDeformer Runtime 执行与 Engine 通用 MeshDeformer 管线对齐，明确“谁创建实例、谁调度、谁在渲染侧消费输出”。

## 2. 关键源码映射
| concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation |
|---|---|---|---|---|---|---|---|
| Deformer 实例创建 | Runtime instance construction | Engine | `D:/UE/UnrealEngine/Engine/Source/Runtime/Engine/Private/Components/SkinnedMeshComponent.cpp` | `USkinnedMeshComponent::CreateMeshDeformerInstances` | infer | 根据 LOD 激活 deformer，创建 `UMeshDeformerInstance` | 切换 LOD 时实例映射应稳定 |
| 资源分配调度 | Resource allocation | Engine | 同上 | `MeshDeformerInstance->AllocateResources()` 调用点 | infer | 在提交工作前分配/验证 GPU 侧资源 | 首帧无资源报错 |
| 工作入队 | Work enqueue | Engine | 同上 | `MeshDeformerInstance->EnqueueWork(...)` 调用点 | infer | 把 deformer 工作提交到执行组（Immediate/EndOfFrame） | 降级分支可触发 |
| Deformer 抽象接口 | Generic deformer contract | Engine | `D:/UE/UnrealEngine/Engine/Source/Runtime/Engine/Classes/Animation/MeshDeformerInstance.h` | `UMeshDeformerInstance::AllocateResources`, `EnqueueWork` | infer | 抽象出各具体 deformer 的统一入口 | 派生类必须实现纯虚接口 |
| 渲染技术切换 | GPUSkin technique switch | Engine | `D:/UE/UnrealEngine/Engine/Source/Runtime/Engine/Private/SkeletalRenderGPUSkin.cpp` | `ESkeletalMeshGPUSkinTechnique::MeshDeformer` 相关分支 | infer | 若存在 deformer instance，渲染路径切到 MeshDeformer 技术 | 观察技术分支切换 |
| 输出缓冲消费 | Output buffer consumption | Engine | 同上 | `GetMeshDeformerInstanceForLOD` + `GetOutputBuffers` | infer | 按输出标志消费位置/法线/颜色等缓冲 | 输出标志错误会导致视觉异常 |

## 3. 分层链路表（L4）
| layer | parent_symbol | child_symbol | file_path | thread_context | data_carrier | failure_point | probe |
|---|---|---|---|---|---|---|---|
| L4 | `USkinnedMeshComponent::CreateMeshDeformerInstances` | `ActiveMeshDeformer->CreateInstance` | `.../SkinnedMeshComponent.cpp` | GameThread | MeshDeformer set + LOD map | LOD 到实例索引错配 | 打印 `InstanceIndexForLOD` |
| L4 | `USkinnedMeshComponent` tick/update | `MeshDeformerInstance->AllocateResources` | `.../SkinnedMeshComponent.cpp` | GameThread -> Render prep | 资源句柄/缓冲描述 | 资源未分配 | 首帧断点验证分配顺序 |
| L4 | `USkinnedMeshComponent` render enqueue | `MeshDeformerInstance->EnqueueWork` | `.../SkinnedMeshComponent.cpp` | GameThread -> RenderThread | `FEnqueueWorkDesc` | 入队失败触发 fallback | 注入无效 provider 验证 fallback |
| L4 | `FSkeletalMeshObjectGPUSkin` setup | `ESkeletalMeshGPUSkinTechnique::MeshDeformer` 分支 | `.../SkeletalRenderGPUSkin.cpp` | RenderThread | 输出缓冲位掩码 | 输出缓冲声明不完整 | 验证位置/法线输出是否齐全 |

## 4. 与上层/下层关系
1. 上层（L3）只关心“模型执行逻辑是否算对”。
2. L4 负责把“算对的结果”通过 Engine 通路提交给渲染系统。
3. 下层（L5）再把实际计算图和 DataProvider 调度展开。

## 5. 可验证探针
1. 在 `USkinnedMeshComponent::CreateMeshDeformerInstances` 断点，验证实例创建时机和 LOD 映射。
2. 在 `SkeletalRenderGPUSkin.cpp` 的 MeshDeformer 分支断点，验证技术切换确实发生。
3. 检查 `GetOutputBuffers()` 返回位掩码是否包含当前模型需要的输出（位置/法线/颜色）。
