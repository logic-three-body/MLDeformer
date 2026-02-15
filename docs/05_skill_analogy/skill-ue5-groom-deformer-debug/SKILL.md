---
name: ue5-groom-deformer-debug
description: Debug UE5 Groom Deformer Graph execution, including control-point domain dispatch, data-interface read/write paths, and visual/performance validation. Use when Groom deformation behaves incorrectly or inconsistently.
---

# UE5 Groom Deformer Debug Skill

## trigger
- Groom 在动画中出现闪烁、错位、形变不连续。
- DeformerGraph 节点输出与期望不一致。
- 需要验证 DataInterface 读写链路是否完整。

## prerequisites
- `HairStrands` 与 `HairStrandsDeformer` 模块可用。
- Groom 资产、Binding、目标角色资源齐全。
- 对应 DeformerGraph 已绑定到 Groom 组件。

## steps
1. 确认执行域：`ControlPoint` / `Curve` 数量与组实例匹配。
2. 检查读取接口：`UOptimusGroomDataInterface` 的位置/属性读取是否有效。
3. 检查写回接口：`UOptimusGroomWriteDataInterface` 的位置/半径/属性写回是否命中。
4. 在图中做最小可视偏移测试，验证写回结果。
5. 比对异常帧与正常帧，定位是数据问题还是图逻辑问题。
6. 复测性能与稳定性，记录回归结果。

## outputs
- 问题定位（执行域、读取、写回、资产或图逻辑）。
- 最小复现步骤。
- 修复建议与复测结论。

## failure_modes
- 组实例为空导致 dispatch 无效。
- 写回缓冲无效或被 fallback 覆盖。
- 绑定关系错误导致控制点映射错位。
- 图内字段与 DataInterface 字段不一致。

## verification
- ControlPoint/Curve 线程数量与资产一致。
- 写回后可见几何变化且无随机闪烁。
- 连续播放下结果稳定，重启后可复现。
