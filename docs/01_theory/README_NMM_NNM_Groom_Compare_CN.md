# NMM / NNM / Groom Deformer 对比（UE5.5）

## 1. 对比总览
| 维度 | NMM (Neural Morph Model) | NNM (Nearest Neighbor Model) | Groom Deformer |
|---|---|---|---|
| 目标 | 学习 Morph 权重 | 学习 + 近邻检索细节 | 控制点级毛发变形 |
| 输入 | 骨骼 + 曲线 | 骨骼 + 曲线（可扩展） | Groom control points / curves |
| 输出 | Morph target weights | 优化网络输出 + 邻域细节融合 | 控制点位置/半径/属性写回 |
| 适用 | 肌肉/皮肤等连续形变 | 衣物褶皱等高频细节 | 毛发导向与局部形态 |
| 训练侧 | Python 训练桥接 + 产物加载 | Python 训练桥接 + 文件缓存 | 以 DeformerGraph 与数据接口为主 |
| 运行侧 | `NetworkInstance->Run()` 后回填权重 | `Execute + RunNearestNeighborModel` | DataInterface 读写 + Dispatch |

## 2. 计算与内存特征
- NMM：输出维度相对可控，适合在线预算受限场景。
- NNM：需要维护邻域数据与额外运行逻辑，质量上限更高但维护成本更大。
- Groom：处理对象是高维控制点流，关键在于数据接口吞吐与图执行稳定性。

## 3. 数据依赖差异
- NMM 依赖高质量 Morph 基底与输入覆盖。
- NNM 额外依赖检索样本质量与分布代表性。
- Groom 依赖导向曲线、分组、插值与控制点属性的一致性。

## 4. 首轮项目选择建议
1. 角色主形变：以 NMM 为主。
2. 高频细节补偿：按需叠加 NNM。
3. 毛发流程：独立维护 Groom Deformer pipeline，避免与角色主变形流程混淆。

## 5. 验证闭环
- 视觉：训练姿态 + 未见姿态 + 极限姿态。
- 性能：`STAT_MLDeformerInference`、GPU Morph 开销、显存占用。
- 稳定性：输入越界、拓扑变化、LOD 切换、热重载后行为。
