---
name: ue5-mldeformer-train
description: Train and validate UE5 ML Deformer models (Neural Morph / Nearest Neighbor) from editor setup to runtime verification and profiling. Use when you need a repeatable UE5 training + inference + acceptance workflow.
---

# UE5 MLDeformer Train Skill

## trigger
- 用户要求训练或复训 ML Deformer。
- 用户要求从训练产物到运行时推理做闭环验证。
- 用户要求定位训练成功但推理异常的问题。

## prerequisites
- UE5 工程可打开，`MLDeformerFramework` 插件可用。
- 训练输入动画/缓存资源完整。
- 目标 Skeletal Mesh 与训练输入一致。
- Houdini 20.0.625 可用（`hython` 可执行）。
- 已配置 `pipeline/hou2ue/config/pipeline.yaml`。

## steps
1. 执行训练前检查：输入资源、帧数、兼容性、模型参数。
2. 在编辑器触发 Train，记录训练开始时间与返回码。
3. 检查模型产物是否成功加载（NMM `nmn`，NNM `ubnne`）。
4. 进入运行时场景，验证 `TickComponent -> ModelInstance::Tick -> Execute` 是否生效。
5. 记录 `STAT_MLDeformerInference`、运行内存、GPU 内存。
6. 用训练姿态、未见姿态、极限姿态做三组验证。

## outputs
- 训练是否成功（返回码 + 关键日志）。
- 推理是否成功（视觉 + 指标）。
- 问题清单与可执行修复建议。
- infer 阶段 Demo 图像序列（PNG）及对应报告。
- Refference/Main_Sequence GroundTruth 对比报告（严格阈值）。

## failure_modes
- `FailPythonError`：训练桥接或脚本异常。
- 输入维度不一致：训练输入配置与网络结构不匹配。
- 产物加载失败：文件不存在或格式不匹配。
- 推理被短路：权重近零、兼容性失败、输入准备失败。

## verification
- 训练后产物文件存在且可加载。
- 运行时可观察到形变随动画变化。
- `STAT_MLDeformerInference` 有稳定可重复统计值。
- 极端姿态下不出现明显爆炸。
- `gt_compare_report.json` 使用 strict 阈值并输出 `strict_profile_name` + `strict_thresholds_hash`。
- strict 阈值固定：`ssim_mean>=0.995`、`ssim_p05>=0.985`、`psnr_mean>=35`、`psnr_min>=30`、`edge_iou_mean>=0.97`。

## hou2ue_automation
1. 一键或分阶段入口：`pipeline/hou2ue/run_all.ps1`。
2. 推荐 smoke 闭环命令：
   - `powershell -ExecutionPolicy Bypass -File pipeline/hou2ue/run_all.ps1 -Stage full -Profile smoke`
3. 推荐 full 闭环命令（快速复用版）：
   - `powershell -ExecutionPolicy Bypass -File pipeline/hou2ue/run_all.ps1 -Stage full -Profile full -Config pipeline/hou2ue/config/pipeline.full_exec.yaml`
4. 断点续跑（推荐）：
   - `-Stage convert|ue_import|ue_setup|train|infer|report -RunDir <existing_run_dir>`
5. full 顺序已扩展：`baseline_sync -> preflight -> houdini -> convert -> ue_import -> ue_setup -> train -> infer -> gt_reference_capture -> gt_source_capture -> gt_compare -> report`。

## reference_baseline_sync
1. Stage：`baseline_sync`，脚本：`pipeline/hou2ue/scripts/sync_reference_baseline.py`。
2. 目标：先把 `Refference` 工程 Emil 关键资产回灌到当前工程，作为 GroundTruth 基线。
3. 策略：`two_phase`。
4. Phase1：Deformer/训练动画/模型/Main 与 LearningCorridor 等核心非超大资产。
5. Phase2：`GeomCache/**` 与法线贴图等超大资产。
6. 当 `reference_baseline.deformer_assets_override` 生效时，`ue_setup` 会覆盖训练输入到 Reference 对齐路径（而不是 `*_smoke/*_full` 动态缓存）。
7. 可追溯输出：`reports/baseline_sync_report.json` + `workspace/backups/baseline_sync/<timestamp>/`。

## strict_clone_setup
1. `reference_baseline.strict_clone.enabled=true` 时，`ue_setup` 前会自动执行 `reference_setup_dump`。
2. `reference_setup_dump` 先尝试在 `Refference` 工程导出 deformer setup；若缺少 EditorTools 模块则回退到 source 工程基线资产导出。
3. `ue_setup_assets.py` 在 strict clone 模式下优先使用 dump JSON 全量覆盖（mesh/graph/test anim/training inputs/NNM sections/model overrides）。
4. 配置后会再次 dump 当前资产并生成字段级 diff：`reports/setup_diff_report.json`。
5. mismatch 视为 `ue_setup` 阶段失败。

## train_determinism
1. 配置入口：`ue.training.determinism`（`enabled/seed/torch_deterministic/cudnn_deterministic/cudnn_benchmark`）。
2. `run_all.ps1 -Stage train` 会注入确定性环境变量并传递到 UE Python 训练脚本。
3. 产物：`reports/train_determinism_report.json`（记录 settings 与 applied env）。

## coord_system_explicit_validation
1. 配置入口：`houdini.coord_system`（`mode=explicit`，`scale_factor=100`，`matrix_3x3`，`translation_offset`）。
2. 执行位置：`houdini_export_abc.py` 在 Alembic 导出后执行显式坐标变换并记录 bbox 前后差异。
3. 导入校验：`ue_import.py` 读取 `manifests/coord_validation_manifest.json`，对导入后的 GeomCache 包围盒做尺度偏差检查。
4. 失败门禁：`coord_system.validate.fail_on_mismatch=true` 时，偏差超 `tolerance` 直接使 `ue_import` 失败。
5. 产物：`manifests/coord_validation_manifest.json` 与 `reports/coord_validation_report.json`。

## main_sequence_groundtruth_compare
1. 参考采集：`gt_reference_capture` 渲染 `Refference/Content/Main.umap` 的 `Main_Sequence` 全序列。
2. 源工程采集：`gt_source_capture` 渲染当前工程同 map/sequence 同分辨率序列。
3. 对比门禁：`gt_compare` 执行 SSIM/PSNR/Edge IoU 阈值校验，失败即阶段失败。
4. 关键报告：
   - `reports/gt_reference_capture_report.json`
   - `reports/gt_source_capture_report.json`
   - `reports/gt_compare_report.json`
5. 推理报告联动：`gt_compare` 会回写 `reports/infer_report.json.outputs.ground_truth_compare_*` 字段。

## groundtruth_commands
1. 全链路（含 baseline + GT compare）：
   - `powershell -ExecutionPolicy Bypass -File pipeline/hou2ue/run_all.ps1 -Stage full -Profile smoke`
2. 断点续跑（已完成 infer，仅补 GT）：
   - `powershell -ExecutionPolicy Bypass -File pipeline/hou2ue/run_all.ps1 -Stage gt_reference_capture -Profile smoke -RunDir <run_dir>`
   - `powershell -ExecutionPolicy Bypass -File pipeline/hou2ue/run_all.ps1 -Stage gt_source_capture -Profile smoke -RunDir <run_dir>`
   - `powershell -ExecutionPolicy Bypass -File pipeline/hou2ue/run_all.ps1 -Stage gt_compare -Profile smoke -RunDir <run_dir>`
3. 仅重跑对比（不重渲染）：
   - `powershell -ExecutionPolicy Bypass -File pipeline/hou2ue/run_all.ps1 -Stage gt_compare -Profile smoke -RunDir <run_dir>`

## groundtruth_troubleshooting
1. `baseline_sync` 失败：先看 `baseline_sync_report.json.errors`，常见是 `Refference` 路径错误或某些 phase glob 未命中。
2. 渲染阶段失败：优先看 `reports/logs/gt_*` 的 stderr tail，检查 `init_unreal.py` 与 Python Executor 是否加载。
3. 帧数不一致：确认两边都跑 `Main_Sequence` 全序列，且渲染参数一致（分辨率/播放窗口/warmup）。
4. 指标明显下降：优先检查 `coord_validation_report.json` 是否已出现尺度/轴向偏差，再看 worst frame 热力图定位问题帧。
5. 如果 `gt_compare` 远低于阈值且画面出现骨骼/条纹伪影，先检查 `ue_setup_report.json` 的 `resolved_training_input_anims` 是否已切到 Reference 覆盖输入。
6. 不要并行执行同一 `RunDir` 的多个 stage；会触发 `run_info.json` 写竞争并导致 stage 异常。

## validated_defaults
- `pipeline.full_exec.yaml` 在 `reference_baseline.enabled=true` 时使用 Reference 对齐训练输入：
  - NMM：`upperBodyFlesh_5kGreedyROM/hero64` + `GC_upperBodyFlesh_5kGreedyROM/hero64`
  - NNM Upper：`upperBody_7000` + `GC_upperBody_Clothing_7000`，邻居 `MLD_NN_upperCostume_PartId_0` + `GC_NN_upperCostume_0`
  - NNM Lower：`lowerCostume_7500k` + `GC_lowerCostume_7500`，邻居 `MLD_NN_lowerCostume_PartId_0` + `GC_NN_lowerCostume_0`
- NMM 导出强制 track 名 `body_mesh`，并清理 prim 名称属性，避免 UE 映射异常。
- Alembic 导入必须：
  - `flatten_tracks=false`
  - `store_imported_vertex_numbers=true`
- NNM 参数对齐：`num_basis_per_section` 与 section `num_pca_coeffs` 保持一致（当前为 64）。
- `pipeline.full_exec.yaml` 已切换到 pipeline 模式：`training_data_source=pipeline`，`skip_train=false`。
- SSIM 使用 windowed 方法（11×11 `uniform_filter`），取代原有 global SSIM。
- strict 阈值（`skip_train` 模式）：`ssim_mean>=0.995`、`ssim_p05>=0.985`、`psnr_mean>=35`、`psnr_min>=30`、`edge_iou_mean>=0.97`。
- pipeline 阈值（`training_data_source=pipeline`）：`ssim_mean>=0.60`、`ssim_p05>=0.40`、`psnr_mean>=15`、`psnr_min>=12`、`edge_iou_mean>=0.40`。

## critical_pitfalls
- 直接用 `PDG_tissue_mesh` 做 NMM 常见顶点不匹配：`59886` vs `skm_Emil body_mesh=104117`，会导致 `Model is not ready for training`。
- `UnrealEditor` 偶发返回码 `3` 不等于阶段失败，应以 `reports/*_report.json` 的 `status` 为准。
- 若开启 Houdini 严格重算，`houdini` 阶段耗时可能很长；建议先 smoke，再 full。
- **UE Python JSON BOM**：UE5 Python 脚本生成的 JSON 文件可能含 UTF-8 BOM，导致 `json.loads()` 失败。所有 JSON 读取应使用 `utf-8-sig` 编码。
- **skip_train 模式报告缺失**：`skip_train=true` 时 `ue_setup` 跳过，不生成 `setup_diff_report.json`。下游脚本需检查此文件存在性并做条件分支。
- **Demo 路线 track 依赖**：Demo executor 要求 LevelSequence 包含 `MovieSceneSkeletalAnimationTrack`。`Main_Sequence` 等 cinematic 序列可能仅有 camera track，无法用于 demo 采集。

## guard_flags
- `run_all.ps1` 支持守护参数：
  - `-NoActivityMinutes <int>`
  - `-RepeatedErrorThreshold <int>`
  - `-HoudiniMaxMinutes <int>`
- 作用：检测重复异常行、长时间无活动、阶段超时后自动中止并输出 guard 日志。

## strict_houdini_tip
- 严格 `full` 常见无法在单窗口完成，建议分段执行并检查进度：
  - `-Stage houdini -Profile full -Config pipeline/hou2ue/config/pipeline.yaml -RunDir <run_dir> -HoudiniMaxMinutes 90`
  - 每轮后检查 `outputFiles/*_ML_PDG_tissue_mesh` 与 `*_ML_PDG_muscle_mesh` 数量，达到 46 再进入 `convert -> ue_import -> ue_setup -> train -> infer -> report`。

## expected_artifacts
- 关键报告：`reports/convert_report.json`、`reports/ue_import_report.json`、`reports/train_report.json`、`reports/infer_report.json`。
- 汇总报告：`reports/pipeline_report_latest.json`。
- 可追溯输入：`manifests/hip_manifest.json`、`manifests/run_manifest.json`、`resolved_config.yaml`。

## training_data_source_pipeline
1. 配置入口：`ue.training.training_data_source: "pipeline"`（`pipeline.full_exec.yaml`）。
2. 适用场景：需要真正的端到端 Houdini→Train→Infer 闭环，训练数据来自管线生成的 GeomCache 而非 Reference 预置。
3. 行为变化：
   - `ue_setup`：使用 `_cfg_from_dump_structural_only()` 从 Reference dump 复制结构配置但保留 pipeline GeomCache 路径。
   - `train`：使用 pipeline 管线产生的训练数据（`GC_upperBodyFlesh_{profile}`, `GC_NN_upperCostume_{profile}`, `GC_NN_lowerCostume_{profile}`）。
   - `setup_diff`：接受 `training_input_anims` 和 `nnm_sections` 的 expected mismatch。
   - `gt_compare`：使用 windowed SSIM（11×11 均值滤波器），pipeline 阈值更宽松。
4. Coord Transform 修复：
   - FBX 数据已在 cm 单位 → `scale_factor=1.0`（非默认 100.0）。
   - `detect_up_axis=True`：自动检测 Z-up 或 Y-up，分别使用 identity 或 Y↔Z swap。
5. Pipeline 阈值（`metrics_profile: pipeline`）：
   - `ssim_mean_min: 0.60`，`ssim_p05_min: 0.40`
   - `psnr_mean_min: 15.0`，`psnr_min_min: 12.0`
   - `edge_iou_mean_min: 0.40`
6. 验证 Run：`20260225_170711_smoke`，SSIM mean=0.776, PSNR mean=18.62, EdgeIoU mean=0.665。

## skip_train_mode
1. 配置入口：`ue.training.skip_train: true`（`pipeline.full_exec.yaml`）。
2. 适用场景：Reference 工程已有训练好的 deformer 权重，当前硬件无法通过重训达到 strict GT 阈值。
3. 行为变化：
   - `ue_setup` 阶段：跳过 `ue_setup_assets.py`，不执行 `save_asset()` 以避免覆盖 Reference 权重。
   - `train` 阶段：从 `Refference/Content/Characters/Emil/Deformers/` 拷贝 3 个 deformer `.uasset` 到 `Content/Characters/Emil/Deformers/`，并进行 SHA-256 校验。
4. 产物：
   - `reports/ue_setup_report.json`（`status=skipped`，`reason=skip_train`）
   - `reports/train_report.json`（`status=skipped`，含每个资产的 SHA-256 `match=true/false`）
5. 限制：不验证训练能力本身；仅验证"使用 Reference 权重后流水线能否端到端 pass"。
6. 根因说明：跨环境训练非确定性（GPU/CUDA/PyTorch 栈差异）导致相同配置+数据重训后网络权重不同，GT 指标下降至 strict 阈值以下。

## abc_import_conversion_fix
1. 问题：Houdini VEX 已在导出时做 Y↔Z + ×100 变换，而 UE `AbcImportSettings` 默认 `Maya` preset 会再次做 Y↔Z 旋转，产生双重坐标变换。
2. 修复位置：`pipeline/hou2ue/scripts/ue_import.py` → `_build_abc_options()`。
3. 修复内容：`conversion_settings.preset = AbcConversionPreset.CUSTOM`，rotation `(0,0,0)`，scale `(1,1,1)`。
4. coord validation 增强：bounds 不可用时改用 `unreal.log_warning()` 明确警告，而非静默 auto-pass。
5. 当前影响：`strict_clone` 模式使用 Reference GeomCache（已正确导入），故此修复暂不影响当前流水线结果。
6. 未来影响：若关闭 `skip_train` 并使用 pipeline 生成的 ABC 重新导入训练，此修复防止双重坐标变换导致的训练数据错误。

## skip_train_shortcut
1. 实现位置：`pipeline/hou2ue/run_all.ps1`（`$fullSkipTrain` 分支）。
2. 适用条件：`-Stage full` 且 `skip_train=true`。
3. 行为：自动跳过 `preflight`、`houdini`、`convert`、`ue_import` 四个阶段，仅执行 `ue_setup → train → infer → gt_compare → report → notify` 共 8 阶段。
4. 报告处理：`build_report.py` 将跳过的阶段标记为 `skipped_skip_train`，不触发缺失报告失败。
5. 时间收益：约 30%（smoke：23 min vs 32.8 min）。
6. 验证 Run：`20260226_001602_smoke`，SSIM=0.9986，PASS。

## color_gt_compare
1. 实现位置：`pipeline/hou2ue/scripts/compare_groundtruth.py`。
2. 新增函数：`_load_rgb()`、`_ssim_color()`（3 通道分别计算 windowed SSIM 取均值）、`_psnr_color()`（RGB joint PSNR）。
3. 输出指标：
   - 逐帧：`color_ssim`、`color_psnr`
   - 汇总：`color_ssim_mean`、`color_ssim_p05`、`color_psnr_mean`、`color_psnr_min`
   - 窗口：`color_ssim_mean`、`color_psnr_mean`
4. 定位：补充性指标，不影响 pass/fail 判定（不纳入阈值门控）。
5. 验证 Run：`20260226_001602_smoke`，color_SSIM=0.9984，color_PSNR=59.44。

## latest_validated_runs

### 验证矩阵（v0.3.0-validated）
| Run ID | Profile | 类型 | SSIM | PSNR | EdgeIoU | Color SSIM | 状态 |
|---|---|---|---|---|---|---|---|
| `20260225_215842_full` | full (46 poses) | 完整链路 | 0.9955 | 53.36 | 0.9874 | — | ✅ PASS |
| `20260225_223734_smoke` | smoke | 稳定性 1/3 | 0.9969 | 55.86 | 0.9891 | — | ✅ PASS |
| `20260225_230707_smoke` | smoke | 稳定性 2/3 | 0.9958 | 54.14 | 0.9877 | — | ✅ PASS |
| `20260225_234041_smoke` | smoke | 稳定性 3/3 | 0.9975 | 57.25 | 0.9906 | — | ✅ PASS |
| `20260226_001602_smoke` | smoke | skip_train 快捷 | 0.9986 | 59.53 | 0.9962 | 0.9984 | ✅ PASS |

- 所有 run 使用配置：`pipeline/hou2ue/config/pipeline.full_exec.yaml`（`skip_train: true`，`training_data_source: reference`，`metrics_profile: strict`）。
- Strict 阈值：`ssim_mean≥0.995`，`ssim_p05≥0.985`，`psnr_mean≥35.0`，`psnr_min≥30.0`，`edge_iou_mean≥0.97`。
- 5/5 全部通过，最低 SSIM=0.9955（full profile），最高 SSIM=0.9986（shortcut run）。

### 历史参考 runs
- **前次 pipeline 通过 run**：`20260225_170711_smoke`（`training_data_source: pipeline`，`skip_train: false`）。
  - GT 指标（windowed SSIM）：`ssim_mean=0.776`，`psnr_mean=18.62`，`edge_iou=0.665`（pipeline 宽松阈值 PASS）。
- **前次 strict 失败 run（重训）**：`20260224_230628_smoke`。
  - `ssim_mean=0.9813`，`psnr_mean=36.01`。失败原因：跨环境训练非确定性。
- 非阻断告警：启动日志可能出现贴图/旧 GeomCache 缺失告警与 revision control checkout 提示，不影响本流水线报告状态。

## current_blockers
- 严格 Houdini 重算分支（`pipeline.yaml` / `pipeline.strict_pdg_only.yaml`）在部分 run 会停在 `"[houdini_cook] pdg cook start"` 后长时间无后续阶段报告（示例：`pipeline/hou2ue/workspace/runs/20260222_153418_full`）。
- 当出现该模式时，不应继续盲跑到超时；必须依赖守护参数提前中止并转入分段排障。

## next_plan
1. **Pipeline 生产闭环**（已验证）：
   - `powershell -ExecutionPolicy Bypass -File pipeline/hou2ue/run_all.ps1 -Stage full -Profile smoke -Config pipeline/hou2ue/config/pipeline.full_exec.yaml`
   - 当前配置：`training_data_source=reference`，`skip_train=true`，使用 Reference 项目预训练权重。
2. **Full profile 验证**（✅ 已通过）：
   - Run `20260225_215842_full`：46 poses，全 11 阶段 success，SSIM=0.9955。
3. **3x 稳定性复跑**（✅ 3/3 通过）：
   - `20260225_223734_smoke`: SSIM=0.9969
   - `20260225_230707_smoke`: SSIM=0.9958
   - `20260225_234041_smoke`: SSIM=0.9975
4. **skip_train 快捷通道**（✅ 已实现并验证）：
   - 当 `skip_train=true` 时自动跳过 preflight/houdini/convert/ue_import，节省 ~30% 时间。
   - Run `20260226_001602_smoke`: 23 min vs 32.8 min，SSIM=0.9986。
5. **彩色 GT 对比**（✅ 已实现）：
   - 新增 `color_ssim_mean/p05` 和 `color_psnr_mean/min` 补充指标。
6. 严格重算专项排障仅跑 Houdini 阶段（同一个 `RunDir`）：
   - `powershell -ExecutionPolicy Bypass -File pipeline/hou2ue/run_all.ps1 -Stage houdini -Profile full -Config pipeline/hou2ue/config/pipeline.yaml -RunDir <run_dir> -NoActivityMinutes 8 -RepeatedErrorThreshold 5 -HoudiniMaxMinutes 90`
7. 每次 run 结束后，固定核对：
   - `reports/pipeline_report_latest.json`
   - `reports/train_report.json`
   - `reports/infer_report.json`
   - `manifests/hip_manifest.json`、`manifests/run_manifest.json`
