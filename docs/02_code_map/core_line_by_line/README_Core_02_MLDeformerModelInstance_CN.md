# Core-02: `MLDeformerModelInstance.cpp` 逐行解析

## 1. 文件定位
- `D:/UE/UnrealEngine/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Source/MLDeformerFramework/Private/MLDeformerModelInstance.cpp`

## 2. 关键行段解析
| line_range | code_focus | explanation | breakpoint_probe |
|---|---|---|---|
| 284-299 | `SetBoneTransforms` | 先 `UpdateBoneTransforms()`，再把每骨骼旋转压成 6 float 写入输入缓冲，`checkfSlow` 防越界。 | 断点 292，验证输入缓冲边界 |
| 301-329 | `SetCurveValues` | 从 AnimInstance 读曲线；无 AnimInstance 时按曲线数补 0。 | 断点 310/321，验证两条分支 |
| 331-346 | `SetNeuralNetworkInputValues` | 按模型能力开关（bones/curves）组合写入输入。 | 关闭某能力后验证偏移变化 |
| 353-372 | `HasValidTransforms` 基础校验 | 保护 `SkeletalMeshComponent` 空指针，检查 LeaderPose 或 BoneSpaceTransform 是否存在。 | 断点 364/369，验证空变换分支 |
| 374-390 | `HasValidTransforms` 资产一致性校验 | 强制当前 SkeletalMesh 与训练输入 SkeletalMesh 一致，避免后续输入结构错配。 | 动态替换 mesh 验证失败路径 |
| 395-402 | `Tick` 后初始化补偿 | 若组件后初始化未完成，运行时重试 `PostMLDeformerComponentInit()`。 | 首帧初始化未完成场景断点 |
| 405-412 | `Tick` 执行主分支 | 要求权重>阈值 + 兼容 + 变换有效 + `SetupInputs()` 成功，才 `Execute()`。 | 断点 405 条件判断 |
| 413-416 | 零权重/失败回退 | 不满足条件则进入 `HandleZeroModelWeight()` 清理/回退路径。 | 权重设 0 验证回退 |
| 418-419 | 后处理钩子 | `PostTick(bExecuteCalled)` 给派生模型统一收尾点。 | 派生类 override 时断点确认 |

## 3. 控制流总结
1. 输入构建由本类统一管理，模型只实现 `SetupInputs/Execute`。
2. 运行前严格校验兼容性和输入可用性，防止推理污染。
3. 回退策略内置，避免“半执行”状态。

## 4. 调试建议
1. 先看 405 行复合条件哪一项失败。
2. 再看 331 行输入写入总量是否等于网络期望。
3. 出现异常形变时，优先验证 374-390 的 mesh 一致性。
