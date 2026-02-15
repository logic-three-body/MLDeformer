# Groom Deformer 理论-源码映射（DeformerGraph / HairStrands）

## 1. 映射表
| concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation |
|---|---|---|---|---|---|---|---|
| 执行域定义 | Control-point domain decomposition | HairStrandsDeformer | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Source/HairStrandsDeformer/Private/DeformerGroomComponentSource.cpp` | `Domains::ControlPoint`, `Domains::Curve` | infer | 定义 DeformerGraph 对 Groom 的执行粒度 | 执行域数量应与组数据一致 |
| 数据读取接口 | Groom feature read DI | HairStrandsDeformer | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Source/HairStrandsDeformer/Private/DeformerDataInterfaceGroom.cpp` | `UOptimusGroomDataInterface` | infer | 暴露位置、半径、根UV、分组等读接口到着色器 | 图内读取字段应与实际属性一致 |
| 数据写回接口 | Groom attribute write DI | HairStrandsDeformer | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Source/HairStrandsDeformer/Private/DeformerDataInterfaceGroomWrite.cpp` | `UOptimusGroomWriteDataInterface` | infer | 将位置/半径/属性写回 DeformedResource | 运行后控制点位置与渲染结果一致 |
| Shader 读模板 | Groom HLSL read template | HairStrands | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Shaders/Private/DeformerDataInterfaceGroom.ush` | `ReadPosition_*`, `ReadGuideIndex_*` | infer | HLSL 侧读取控制点和导向映射 | GPU 调试输出值应合理 |
| Shader 写模板 | Groom HLSL write template | HairStrands | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Shaders/Private/DeformerDataInterfaceGroomWrite.ush` | `WritePosition_*`, `WriteRadius_*` | infer | HLSL 侧写回控制点位置和半径 | 写回后无越界、无闪烁 |
| 变形骨架构建 | Groom-to-skeletal conversion | HairStrandsCore | `D:/UE/UnrealEngine/Engine/Plugins/Runtime/HairStrands/Source/HairStrandsCore/Private/GroomDeformerBuilder.cpp` | `BuildSkeletalMesh`, `BuildSkeletonBones`, `BuildMeshSection`, `CreateSkeletalMesh` | train/asset build | 将 Groom 导向结构构建为可驱动骨架与网格资产 | 生成 skeletal mesh / skeleton / physics asset 成功 |

## 2. 主链路理解
1. `GroomComponentSource` 决定图执行域与线程粒度。
2. `GroomDataInterface` 负责读入控制点与曲线属性。
3. 图节点计算后通过 `GroomWriteDataInterface` 写回 deformed buffer。
4. 渲染阶段消费写回后的控制点数据完成最终显示。

## 3. 与论文/理论的对应
- 理论中的“高维控制点空间”在引擎内对应 `ControlPoint` 执行域。
- 理论中的“导向关系/插值”在引擎内对应 `GuideIndex`、插值缓冲与曲线映射。
- 理论中的“重建输出”在引擎内对应 DataInterface 写回阶段。

## 4. 最小验证
1. 在 DeformerGraph 中做可控偏移，确认写回链路可见。
2. 对同一 Groom 在静态/动画下观察是否出现不连续跳变。
3. 验证 Group/Curve/ControlPoint 数量与图执行维度一致。
