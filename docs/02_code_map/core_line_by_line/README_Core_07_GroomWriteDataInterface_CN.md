# Core-07: `DeformerDataInterfaceGroomWrite.cpp` 逐行解析

## 1. 文件定位
- `D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Source/HairStrandsDeformer/Private/DeformerDataInterfaceGroomWrite.cpp`

## 2. 关键行段解析（接口定义层）
| line_range | code_focus | explanation | breakpoint_probe |
|---|---|---|---|
| 55-64 | `GetSupportedInputs` | 暴露输入函数：`ReadNumControlPoints` / `ReadNumCurves`。 | 断点确认函数签名注册 |
| 66-112 | `GetSupportedOutputs` | 注册写接口（Position/Radius/RootUV/Color 等），决定图节点可写能力。 | 对照图节点输出 pin |
| 114-122 | Shader 参数结构 | 定义 `FGroomWriteDataInterfaceParameters`：包含 Common + SRV/UAV。 | 检查参数结构体大小 |
| 129-133 | `TemplateFilePath` | 绑定 `.ush` 模板路径。 | 模板路径错误时应直接暴露 |
| 141-150 | `GetHLSL` | 读取模板并注入 DataInterface 名称生成 HLSL。 | 断点查看最终 HLSL 字符串 |
| 153-158 | `CreateDataProvider` | 以 `UGroomComponent` + `OutputMask` 构建 provider。 | 检查 OutputMask 传递 |

## 3. 关键行段解析（RenderProxy 层）
| line_range | code_focus | explanation | breakpoint_probe |
|---|---|---|---|
| 168-176 | proxy 构造 | 读取 Groom group instance，建立 `Instances` 列表。 | 验证 group 数与 invocations 一致 |
| 178-189 | `IsValid` | 校验参数结构大小和调用数匹配。 | 故意错参数触发 false |
| 192-204 | `AllocateResources` 开场 | 按每个 group 申请资源，准备 fallback SRV/UAV。 | 断点检查 fallback buffer |
| 209-220 | Position/Radius 缓冲 | `OutputMask` 开启时绑定真实缓冲，否则绑定 dummy。 | 切换 mask 验证分支 |
| 223-241 | Curve 属性缓冲 | 写属性前先从 rest 复制，保证未写字段保持一致。 | 断点看 `AddCopyBufferPass` |
| 244-257 | Point 属性缓冲 | 同样按 mask 决定真实或 fallback 缓冲。 | 验证 point attribute 生效 |
| 263-265 | `GatherDispatchData` 入场 | 构造参数视图并按 invocation 写参数。 | 看 `ParameterArray.Num()` |
| 272-283 | 参数写入 | 校验关键 SRV/UAV 是否有效，写入 Common 和各缓冲句柄。 | GPU capture 验证参数绑定 |

## 4. 控制流总结
1. 此文件负责“把 Groom 写回能力暴露给 Compute kernel”。
2. 关键稳定点在 `IsValid`、`OutputMask` 分支、fallback 缓冲。
3. 视觉异常大多来自 `AllocateResources` 资源绑定或 `GatherDispatchData` 参数装填错误。

## 5. 调试建议
1. 先看 `IsValid` 是否通过。
2. 再看 `OutputMask` 是否覆盖预期输出字段。
3. 最后核对 `.ush` 写函数和本文件参数绑定是否一致。
