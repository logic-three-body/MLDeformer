# Core-01: `MLDeformerComponent.cpp` 逐行解析

## 1. 文件定位
- `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFramework/Private/MLDeformerComponent.cpp`

## 2. 关键行段解析
| line_range | code_focus | explanation | breakpoint_probe |
|---|---|---|---|
| 25-32 | 构造函数默认行为 | 设定 Tick 组 `TG_PrePhysics`、编辑器可 Tick、自动激活。说明 MLDeformer 在骨骼更新前参与。 | 断点构造函数，确认组件默认参数 |
| 34-43 | `Init()` 无资产分支 | 无 `DeformerAsset` 时立即释放实例并返回，避免悬挂状态。 | 清空资产后调用 `Init()`，验证 `ReleaseModelInstance()` |
| 45-55 | `Init()` 正常建模分支 | 读取模型、重建 `ModelInstance`、`Init(SkelMeshComponent)`、`PostMLDeformerComponentInit()`、绑定委托。 | 断点 50/53，确认实例创建与后初始化顺序 |
| 63-89 | `SetupComponent()` 切换组件 | 先 `RenderCommandFence` 同步，再移除/添加 Tick 前置依赖，更新 `DeformerAsset` 和 `SkelMeshComponent`。 | 热切换 SkelMeshComponent，观察依赖链 |
| 91-106 | DeformerGraph 缺失告警 | 模型声明了默认图但组件没有 Mesh Deformer 时发 warning，提示退化到线性蒙皮。 | 人为去掉 Mesh Deformer，观察日志 |
| 114-124 | `BindDelegates()` | 绑定 `ReinitModelInstance` 回调，模型请求重建时可触发 `Init()`。 | 触发模型重建委托，确认回调生效 |
| 131-138 | `UnbindDelegates()` | 销毁/切换前解除委托，防止回调访问失效对象。 | 销毁前检查 handle 是否被清理 |
| 148-154 | `ReleaseModelInstance()` | 强制 `ConditionalBeginDestroy()` 并置空，避免等待 GC。 | 反复激活/停用后检查实例泄漏 |
| 226-233 | `TickComponent()` 前置检查 | 记录 `STAT_MLDeformerInference`，跳过 PauseTick。 | `stat MLDeformer` 看统计是否稳定 |
| 235-244 | 运行时执行条件 | 同时要求 `ModelInstance`、`Model`、`SkelMeshComponent` 有效且 LOD 小于模型支持上限，再调用 `ModelInstance->Tick(...)`。 | 切 LOD 超阈值，验证不执行路径 |
| 245-252 | Editor 内存更新 | 仅编辑器下按需更新模型内存统计。 | 触发 `IsMemUsageInvalidated()` 验证更新 |

## 3. 控制流总结
1. 生命周期：`SetupComponent` -> `Init` -> `TickComponent`。
2. 保护策略：空资产、无模型、无组件、LOD 超限全部有前置保护。
3. 可观测性：`STAT_MLDeformerInference` + `TRACE_CPUPROFILER_EVENT_SCOPE`。

## 4. 调试建议
1. 首先验证是否进入 235 行条件块。
2. 再验证 `ModelInstance->Tick` 是否被调用。
3. 若无执行，优先看 LOD 和资产/组件绑定。
