# L1 模块启动与系统装配（Module Startup）

## 1. 目标
说明 MLDeformer、Optimus、ComputeFramework 在 UE 启动后如何注册能力，形成后续训练与推理入口。

## 2. 关键源码
| concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation |
|---|---|---|---|---|---|---|---|
| MLDeformer Runtime 模块注册 | System bootstrapping | MLDeformerFramework | `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFramework/Private/MLDeformerModule.cpp` | `IMPLEMENT_MODULE(UE::MLDeformer::FMLDeformerModule, MLDeformerFramework)` | both | 注册 Runtime 模块入口，挂载全局初始化逻辑 | 启动编辑器后检查模块可加载 |
| MLDeformer Runtime 启动 | Startup lifecycle | MLDeformerFramework | 同上 | `FMLDeformerModule::StartupModule` | both | 运行时初始化，准备后续资产/组件行为 | 在模块启动阶段下断点 |
| MLDeformer Editor 模块注册 | Editor integration | MLDeformerFrameworkEditor | `.../MLDeformerFrameworkEditor/Private/MLDeformerEditorModule.cpp` | `IMPLEMENT_MODULE(UE::MLDeformer::FMLDeformerEditorModule, MLDeformerFrameworkEditor)` | train | 注入编辑器工具、菜单、细节面板 | 打开 MLDeformer 资产确认工具页可用 |
| MLDeformer Editor 启动 | Toolkit wiring | MLDeformerFrameworkEditor | 同上 | `FMLDeformerEditorModule::StartupModule` | train | 训练面板与资产编辑器链路装配 | 进入资产编辑器时能创建 toolkit |
| Optimus Core 模块注册 | DeformerGraph runtime base | OptimusCore | `D:/UE/UnrealEngine/Engine/Plugins/Animation/DeformerGraph/Source/OptimusCore/Private/OptimusCoreModule.cpp` | `IMPLEMENT_MODULE(FOptimusCoreModule, OptimusCore)` | infer | DataInterface/Graph 核心类型注册 | `OptimusCore` 模块加载状态正常 |
| Optimus Core 启动 | Type registry setup | OptimusCore | 同上 | `FOptimusCoreModule::StartupModule` | infer | 注册数据类型、节点、图执行所需基础设施 | 节点类型可在图中创建 |
| ComputeFramework Runtime 模块注册 | Compute graph runtime | ComputeFramework | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/ComputeFramework/Source/ComputeFramework/Private/ComputeFrameworkModule.cpp` | `IMPLEMENT_MODULE(FComputeFrameworkModule, ComputeFramework)` | infer | 提供通用 ComputeGraph 运行层 | `ComputeFramework` 模块加载成功 |
| ComputeFramework 启动 | Runtime feature setup | ComputeFramework | 同上 | `FComputeFrameworkModule::StartupModule` | infer | 准备图资源更新、调度环境 | 构建图资源时不报模块缺失 |

## 3. 分层链路表（L1）
| layer | parent_symbol | child_symbol | file_path | thread_context | data_carrier | failure_point | probe |
|---|---|---|---|---|---|---|---|
| L1 | `IMPLEMENT_MODULE(...MLDeformerFramework...)` | `FMLDeformerModule::StartupModule` | `.../MLDeformerModule.cpp` | Engine init thread | Module manager state | 模块未启用或依赖缺失 | 用 `LogModuleManager` 检查加载日志 |
| L1 | `IMPLEMENT_MODULE(...MLDeformerFrameworkEditor...)` | `FMLDeformerEditorModule::StartupModule` | `.../MLDeformerEditorModule.cpp` | Editor startup | Editor toolkit registries | 编辑器扩展未注册 | 打开资产编辑器确认 toolkit 存在 |
| L1 | `IMPLEMENT_MODULE(...OptimusCore...)` | `FOptimusCoreModule::StartupModule` | `.../OptimusCoreModule.cpp` | Engine init thread | DataType/Node registries | 图节点注册失败 | 在图中搜索核心节点类型 |
| L1 | `IMPLEMENT_MODULE(...ComputeFramework...)` | `FComputeFrameworkModule::StartupModule` | `.../ComputeFrameworkModule.cpp` | Engine init thread | Compute graph runtime services | ComputeGraph 无法执行 | 创建最小图并执行一次 Dispatch |

## 4. 这一层解决什么问题
1. 解释“为什么同一套符号在 Editor 和 Runtime 分离”。
2. 解释“MLDeformer 运行依赖 Optimus/ComputeFramework”的装配顺序。
3. 给后续 L2-L7 提供固定入口（模块可用性先决条件）。

## 5. 可验证探针
1. 在 `FMLDeformerEditorModule::StartupModule` 打断点，验证编辑器扩展已注入。
2. 在 `FComputeFrameworkModule::StartupModule` 打断点，验证 ComputeFramework 先于图执行初始化。
3. 启用 `LogModuleManager Verbose`，确认 `MLDeformerFramework` / `OptimusCore` / `ComputeFramework` 都被加载。
