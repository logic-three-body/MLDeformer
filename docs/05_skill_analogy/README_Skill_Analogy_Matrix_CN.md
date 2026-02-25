# Skill 类比矩阵（本仓库版）

## 1. 目标
在 `docs/references` 已移除后，保留本仓库可执行的 skill 入口，并将理论/源码文档映射到本地 skill 草案与 prototype 流程。

## 2. 本地可用 skill
- `docs/05_skill_analogy/skill-ue5-mldeformer-train/SKILL.md`
- `docs/05_skill_analogy/skill-ue5-groom-deformer-debug/SKILL.md`
- `docs/05_skill_analogy/skill-prototype-data-acquisition/SKILL.md`
- `docs/05_skill_analogy/skill-prototype-wsl-train-orchestrator/SKILL.md`
- `docs/05_skill_analogy/skill-prototype-win-infer-viz/SKILL.md`

## 3. 类比矩阵
| 理论/工程主题 | 文档入口 | 建议 skill | 使用时机 | 输出结果 |
|---|---|---|---|---|
| 训练到推理主链打通 | `docs/02_code_map/deep_dive/README_UE5_TopDown_Source_Atlas_CN.md` | `docs/05_skill_analogy/skill-ue5-mldeformer-train/SKILL.md` | 首次跑通完整链路 | 一次可复用的 Train/Infer 流程 |
| 训练前检查与失败回退 | `docs/04_train_infer/README_UE5_MLDeformer_TrainInfer_CN.md` | `docs/05_skill_analogy/skill-ue5-mldeformer-train/SKILL.md` | 训练失败、产物加载失败时 | 可追踪的检查清单与回退步骤 |
| Demo 采集路线调试 | `docs/memory/checkpoint-20260225-strict-reference-pipeline-pass.md` | `docs/05_skill_analogy/skill-ue5-mldeformer-train/SKILL.md` | Demo executor 报错、动画替换失败时 | MovieSceneSkeletalAnimationTrack 依赖约束 |
| Report 阶段编码问题 | `docs/memory/checkpoint-20260225-strict-reference-pipeline-pass.md` | `docs/05_skill_analogy/skill-ue5-mldeformer-train/SKILL.md` | JSON 解析报错、BOM 编码异常时 | UTF-8-sig 编码修复方案 |
| Groom 图调试 | `docs/02_code_map/deep_dive/README_L6_DataInterface_Groom_CN.md` | `docs/05_skill_analogy/skill-ue5-groom-deformer-debug/SKILL.md` | 图执行异常、写回不生效时 | 可定位的 Debug 路径 |
| Shader/RDG 验证 | `docs/02_code_map/deep_dive/README_L7_Shader_RDG_Profiling_CN.md` | `docs/05_skill_analogy/skill-ue5-groom-deformer-debug/SKILL.md` | 需要检查 Dispatch/参数写入 | 关键探针与验证证据 |
| skip_train 快捷通道 | `docs/memory/checkpoint-20260226-full-validation-and-optimizations.md` | `docs/05_skill_analogy/skill-ue5-mldeformer-train/SKILL.md` | skip_train=true 时想缩短 full 链路耗时 | 跳过 4 阶段，节省 ~30% 时间 |
| 彩色 GT 对比指标 | `docs/memory/checkpoint-20260226-full-validation-and-optimizations.md` | `docs/05_skill_analogy/skill-ue5-mldeformer-train/SKILL.md` | 灰度 SSIM 不足以区分色差漂移时 | color_SSIM/color_PSNR 补充指标 |
| 原型数据获取与清洗 | `prototype/README.md` | `docs/05_skill_analogy/skill-prototype-data-acquisition/SKILL.md` | 需要快速构建外置数据根并产出清单 | 资产状态 + 数据QC |
| WSL 训练编排 | `prototype/README.md` | `docs/05_skill_analogy/skill-prototype-wsl-train-orchestrator/SKILL.md` | 需要多方法 smoke 训练 | 统一训练报告 |
| Windows 推理可视化 | `prototype/README.md` | `docs/05_skill_analogy/skill-prototype-win-infer-viz/SKILL.md` | 需要生成误差/时延图表 | 推理报告 + 对比图 |

## 4. 使用建议
1. 先从 `docs/README.md` 进入对应层级文档。
2. UE 引擎内链路优先使用两个 UE skill。
3. 跨平台原型验证优先使用三个 prototype skill。
4. 每次调优都记录 `STAT_MLDeformerInference` 和关键失败路径。
5. **新增故障模式参考**：
   - Demo 采集失败 → 检查是否使用了缺少 `MovieSceneSkeletalAnimationTrack` 的 LevelSequence
   - JSON 解析异常 → 优先检查是否为 UTF-8 BOM 编码问题（使用 `utf-8-sig`）
   - skip_train 模式报告缺失 → 检查下游脚本是否有条件分支处理跳过的阶段
   - skip_train 快捷通道未生效 → 确认 `-Stage full` 且 config 中 `skip_train: true`，否则不触发阶段跳过
   - 彩色 GT 指标缺失 → 确认 `compare_groundtruth.py` 已包含 `_load_rgb()`/`_ssim_color()`/`_psnr_color()`
