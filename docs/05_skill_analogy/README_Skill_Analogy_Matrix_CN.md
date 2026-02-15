# 理论章节 ↔ 现有 skill 类比矩阵

## 1. 目标
把本项目文档中的理论与工程环节，映射到 `docs/references/docs/skill` 已有技能，形成“学什么 -> 用哪个 skill”的直接路径。

## 2. 类比矩阵
| 理论/工程主题 | 文档入口 | 可类比 skill | 使用时机 | 备注 |
|---|---|---|---|---|
| 训练-推理全流程闭环 | `docs/04_train_infer/README_UE5_MLDeformer_TrainInfer_CN.md` | `docs/references/docs/skill/mimickit-allcase-e2e-skill/SKILL.md` | 需要快速打通端到端流程时 | 重点借鉴流程编排思路 |
| 长周期任务管理 | `docs/04_train_infer/README_Profiling_And_Debug_CN.md` | `docs/references/docs/skill/mimickit-allcase-longcycle-skill/SKILL.md` | 训练任务长时间运行时 | 借鉴保活与阶段化推进 |
| DeepMimic 式训练组织方法 | `docs/02_code_map/README_UE5_CodeMap_Mainline_CN.md` | `docs/references/docs/skill/mimickit-deepmimic-training-skill/SKILL.md` | 构建训练脚本规范时 | 借鉴训练阶段拆分 |
| 多 case 性能对比 | `docs/04_train_infer/README_Profiling_And_Debug_CN.md` | `docs/references/docs/skill/mimickit-multicase-gpu-util-skill/SKILL.md` | 需要横向比较 GPU 利用率时 | 借鉴基准记录模板 |
| 双卡训练策略 | `docs/04_train_infer/README_Profiling_And_Debug_CN.md` | `docs/references/docs/skill/mimickit-piplus-dualgpu-training-skill/SKILL.md` | 多 GPU 调优时 | 借鉴降级与回退策略 |
| 代码历史追踪 | `docs/02_code_map/README_UE5_CodeMap_Mainline_CN.md` | `docs/references/docs/skill/mimickit-framework-usage-from-git-history/SKILL.md` | 需要追踪框架行为演进时 | 借鉴“从 git 历史定位行为”的方法 |
| 多后端环境准备 | `docs/03_dataset_pipeline/README_Houdini_to_UE_Dataset_CN.md` | `docs/references/docs/skill/mimickit-wsl-multi-backend-setup-skill/SKILL.md` | 环境切换与依赖排查时 | 借鉴环境基线检查法 |

## 3. 新增 UE 专用 skill 草案
- `docs/05_skill_analogy/skill-ue5-mldeformer-train/SKILL.md`
- `docs/05_skill_analogy/skill-ue5-groom-deformer-debug/SKILL.md`

## 4. 使用建议
1. 先按本仓库文档理解 UE5 机制，再用类比 skill 的流程化经验落地执行。
2. 不直接照搬 MimicKit 参数，重点迁移“流程组织、验收标准、回退策略”。
3. 对 UE 专用场景优先使用本仓库新增的两个 skill 草案。
