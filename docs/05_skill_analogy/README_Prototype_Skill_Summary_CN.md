# Prototype Skill 总结（MLDeformer）

## 1. 目标
将 `prototype/` 的全流程沉淀成可复用 skill，支持后续研究快速复现与排障。

## 2. Skill 清单（UE + Prototype）
| skill | 文件 | 适用阶段 | 关键输出 |
|---|---|---|---|
| UE 训练闭环 | `docs/05_skill_analogy/skill-ue5-mldeformer-train/SKILL.md` | UE Editor 训练/运行时验证 | 可复现 Train/Infer 检查结果 |
| UE Groom 调试 | `docs/05_skill_analogy/skill-ue5-groom-deformer-debug/SKILL.md` | Groom Deformer 图与 RDG 调试 | 可定位的图执行问题路径 |
| Prototype 数据获取与清洗 | `docs/05_skill_analogy/skill-prototype-data-acquisition/SKILL.md` | 数据准备 | 资产状态文件、`dataset_manifest.jsonl` |
| Prototype WSL 训练编排 | `docs/05_skill_analogy/skill-prototype-wsl-train-orchestrator/SKILL.md` | 训练执行 | `train_report.json`、训练索引 |
| Prototype Windows 推理可视化 | `docs/05_skill_analogy/skill-prototype-win-infer-viz/SKILL.md` | 推理与结果分析 | `infer_report.json`、可视化图表 |

## 3. 触发信号
1. 新增数据源或更换资产配方。
2. 需要重新跑 smoke 训练验证环境。
3. 需要比对 NMM/NNM/Groom 推理误差与延迟。

## 4. 成功判据
1. `prototype/state/assets_status.json` 里公开资源可下载，受限资源出现 `manual_pending` 时流程不中断。
2. `D:/MLDPrototypeData/processed/dataset_manifest.jsonl` 存在且包含 `qc_status`。
3. `D:/MLDPrototypeData/artifacts/train/*/train_report.json` 与 `D:/MLDPrototypeData/artifacts/infer/*/infer_report.json` 均存在。
4. Notebook 能画出误差和时延柱状图。

## 5. 常见失败与回退
1. 公开资源 URL 失效：更新 `assets.manifest.yaml` 的下载地址后重跑 `fetch_public_assets.py`。
2. 受限资源无凭据：保持 `manual_pending`，先用公开资源完成流水线，再人工补登。
3. WSL 训练环境缺包：先跑 `bootstrap_wsl.sh`，确认 conda/env 激活状态。
4. 推理缺训练产物：检查 `train_report.json` 路径后重跑 `train_wsl.sh smoke`。

## 6. 与 UE 文档映射
- 训练链路映射：`docs/02_code_map/README_NMM_TheoryCode_CN.md`
- Runtime 主链：`docs/02_code_map/deep_dive/README_L3_Runtime_Infer_CN.md`
- Groom 底层映射：`docs/02_code_map/README_GroomDeformer_TheoryCode_CN.md`

## 7. 本轮结项状态
1. 新增 3 个 prototype 专用 skill，覆盖数据、训练、推理可视化。
2. 保留 2 个 UE 专用 skill，形成“引擎链路 + 跨平台原型链路”双轨。
3. 已完成 `run_all.ps1 -Stage full` 跑通验证，生成数据清单、训练报告、推理报告三类产物。
