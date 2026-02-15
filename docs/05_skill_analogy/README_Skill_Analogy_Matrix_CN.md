# Skill 类比矩阵（本仓库版）

## 1. 目标
在 `docs/references` 已移除后，保留本仓库可执行的 skill 入口，并将理论/源码文档映射到本地 skill 草案。

## 2. 本地可用 skill
- `docs/05_skill_analogy/skill-ue5-mldeformer-train/SKILL.md`
- `docs/05_skill_analogy/skill-ue5-groom-deformer-debug/SKILL.md`

## 3. 类比矩阵
| 理论/工程主题 | 文档入口 | 建议 skill | 使用时机 | 输出结果 |
|---|---|---|---|---|
| 训练到推理主链打通 | `docs/02_code_map/deep_dive/README_UE5_TopDown_Source_Atlas_CN.md` | `docs/05_skill_analogy/skill-ue5-mldeformer-train/SKILL.md` | 首次跑通完整链路 | 一次可复用的 Train/Infer 流程 |
| 训练前检查与失败回退 | `docs/04_train_infer/README_UE5_MLDeformer_TrainInfer_CN.md` | `docs/05_skill_analogy/skill-ue5-mldeformer-train/SKILL.md` | 训练失败、产物加载失败时 | 可追踪的检查清单与回退步骤 |
| Groom 图调试 | `docs/02_code_map/deep_dive/README_L6_DataInterface_Groom_CN.md` | `docs/05_skill_analogy/skill-ue5-groom-deformer-debug/SKILL.md` | 图执行异常、写回不生效时 | 可定位的 Debug 路径 |
| Shader/RDG 验证 | `docs/02_code_map/deep_dive/README_L7_Shader_RDG_Profiling_CN.md` | `docs/05_skill_analogy/skill-ue5-groom-deformer-debug/SKILL.md` | 需要检查 Dispatch/参数写入 | 关键探针与验证证据 |

## 4. 使用建议
1. 先从 `docs/README.md` 进入对应层级文档。
2. 需要执行步骤时，优先套用本地两个 UE skill。
3. 每次调优都记录 `STAT_MLDeformerInference` 和关键失败路径。
