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
- infer 阶段 `infer_demo_report.json` 为 `success`，且每个作业输出帧数达到配置阈值（默认 120）。
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
5. infer 出图默认已并入 `-Stage infer`，无需单独 stage。
6. full 顺序已扩展：`baseline_sync -> preflight -> houdini -> convert -> ue_import -> ue_setup -> train -> infer -> gt_reference_capture -> gt_source_capture -> gt_compare -> report`。

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
- infer demo 子流程还支持配置守护（`ue.infer.demo.timeout/guard`），用于单作业提前中止，避免盲跑到超时。

## infer_demo_route
1. infer 阶段新增子流程：`ue_demo_capture.py -> ue_infer.py`。
2. 默认路线：
   - `nmm_flesh`：`/Game/Global/DemoRoom/LevelSequences/LS_NMM_Local`
   - `nnm_upper`：`/Game/Global/DemoRoom/LevelSequences/LS_NearestNeighbour`
3. 默认动画源：`ue.infer.test_animations`（box/jog/rom 三条）。
4. 默认输出规格：`PNG 1280x720`，每段 `120` 帧，覆盖 `2 routes x 3 anims = 6 jobs`。
5. UE runtime executor 实现位于：
   - `Content/Python/init_unreal.py`
   - `Content/Python/Hou2UeDemoRuntimeExecutor.py`
6. **Demo 路线约束**：Demo executor 的 `_swap_sequence_animation()` 要求目标 LevelSequence 包含 `MovieSceneSkeletalAnimationTrack`。`Main_Sequence` 不包含此 track（仅用于 GT 采集的 cinematic 序列），因此 demo 路线必须使用 DemoRoom 序列。

## infer_demo_artifacts
1. 总报告：`reports/infer_demo_report.json`
2. infer 汇总：`reports/infer_report.json`（包含 demo 摘要字段）
3. 单作业报告：`reports/infer_demo_jobs/*.json`
4. 作业日志：`reports/logs/infer_demo/*.stdout.log`、`reports/logs/infer_demo/*.stderr.log`
5. 图像序列目录：
   - `workspace/staging/<profile>/ue_demo/<route>/<anim>/frames/*.png`

## infer_demo_acceptance
1. `infer_demo_report.json.status == success`。
2. `jobs_summary.total == 6` 且 `failed == 0`（默认配置）。
3. 每个 job `frame_count >= 120`（默认 `clip_frames`）。
4. `infer_report.json.outputs.demo_capture_status == success`。

## infer_demo_troubleshooting
1. `Missing executor`：检查 `Content/Python/init_unreal.py` 是否导入 `Hou2UeDemoRuntimeExecutor`，以及启动参数是否包含 `-ExecutorPythonClass=/Engine/PythonTypes.Hou2UeDemoRuntimeExecutor`。
2. `bad sequence/animation`：核对 `ue.infer.demo.routes[].level_sequence` 与 `ue.infer.test_animations` 路径是否可加载。
3. `repeated error abort`：提高 `ue.infer.demo.guard.repeated_error_threshold` 或先修复首个重复异常行。
4. `timeout/no activity abort`：调整 `ue.infer.demo.timeout.per_job_minutes` 与 `ue.infer.demo.timeout.no_activity_minutes`，并检查渲染进程是否实际有输出。
5. `MovieSceneSkeletalAnimationTrack not found`：Demo executor 无法在目标 LevelSequence 中找到骨骼动画 track。确认使用的 LevelSequence 包含 `MovieSceneSkeletalAnimationTrack`（如 DemoRoom 的 `LS_NMM_Local`/`LS_NearestNeighbour`），而非仅有 camera cut track 的 cinematic 序列（如 `Main_Sequence`）。

## infer_demo_commands
1. 仅跑 infer（含 demo 出图）：
   - `powershell -ExecutionPolicy Bypass -File pipeline/hou2ue/run_all.ps1 -Stage infer -Profile smoke -RunDir <run_dir>`
2. 全链路（含 demo 出图）：
   - `powershell -ExecutionPolicy Bypass -File pipeline/hou2ue/run_all.ps1 -Stage full -Profile smoke`
3. full_exec 配置全链路：
   - `powershell -ExecutionPolicy Bypass -File pipeline/hou2ue/run_all.ps1 -Stage full -Profile full -Config pipeline/hou2ue/config/pipeline.full_exec.yaml`

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

## latest_validated_runs
- **最新 skip_train 通过 run**：`pipeline/hou2ue/workspace/runs/20260225_194534_smoke`。
  - 使用配置：`pipeline/hou2ue/config/pipeline.full_exec.yaml`（`skip_train: true`，`training_data_source: reference`）。
  - profile: `smoke`。
  - 全阶段状态：all 11 stages = success。
  - Demo 采集：6 jobs (2 routes × 3 anims)，720 frames。
  - GT 指标：`ssim_mean=0.9955`，`ssim_p05=0.9953`，`psnr_mean=53.36`，`psnr_min=52.21`，`edge_iou=0.987`。
  - 关键修复：demo 路线回退到 DemoRoom，BOM 编码修复，build_report.py 守卫，阈值对齐。
- **前次 pipeline 通过 run**：`pipeline/hou2ue/workspace/runs/20260225_170711_smoke`。
  - 使用配置：`pipeline/hou2ue/config/pipeline.full_exec.yaml`（`training_data_source: pipeline`，`skip_train: false`）。
  - GT 指标（windowed SSIM）：`ssim_mean=0.776`，`ssim_p05=0.697`，`psnr_mean=18.62`，`psnr_min=15.29`，`edge_iou=0.665`。
  - Coord transforms：flesh=Z-up identity, NNM upper=Y-up→Z-up swap, NNM lower=Z-up identity。
- **前次 skip_train run（参考）**：`pipeline/hou2ue/workspace/runs/20260225_122128_smoke`。
  - GT 指标（global SSIM）：`ssim_mean=0.9997`，`ssim_p05=0.9996`，`psnr_mean=53.61`，`psnr_min=52.28`，`edge_iou=0.9875`。
- **前次 strict 失败 run（重训）**：`pipeline/hou2ue/workspace/runs/20260224_230628_smoke`。
  - GT 指标：`ssim_mean=0.9813`，`ssim_p05=0.9523`，`psnr_mean=36.01`，`psnr_min=29.38`，`edge_iou=0.9697`。
  - 失败原因：跨环境训练非确定性。
- 非阻断告警：启动日志可能出现贴图/旧 GeomCache 缺失告警与 revision control checkout 提示，不影响本流水线报告状态。

## current_blockers
- 严格 Houdini 重算分支（`pipeline.yaml` / `pipeline.strict_pdg_only.yaml`）在部分 run 会停在 `"[houdini_cook] pdg cook start"` 后长时间无后续阶段报告（示例：`pipeline/hou2ue/workspace/runs/20260222_153418_full`）。
- 当出现该模式时，不应继续盲跑到超时；必须依赖守护参数提前中止并转入分段排障。

## next_plan
1. **Pipeline 生产闭环**（已验证）：
   - `powershell -ExecutionPolicy Bypass -File pipeline/hou2ue/run_all.ps1 -Stage full -Profile smoke -Config pipeline/hou2ue/config/pipeline.full_exec.yaml`
   - 当前配置：`training_data_source=pipeline`，`skip_train=false`，使用管线生成 GeomCache 训练。
2. **Full profile 验证**（待做）：
   - 切换 `-Profile full` 运行完整 PDG Cook + 训练。
3. **3x 稳定性复跑**（待验证）：
   - 连续 3 轮 smoke 全链路，验收：3/3 pipeline pass。
4. 严格重算专项排障仅跑 Houdini 阶段（同一个 `RunDir`）：
   - `powershell -ExecutionPolicy Bypass -File pipeline/hou2ue/run_all.ps1 -Stage houdini -Profile full -Config pipeline/hou2ue/config/pipeline.yaml -RunDir <run_dir> -NoActivityMinutes 8 -RepeatedErrorThreshold 5 -HoudiniMaxMinutes 90`
5. 每次 run 结束后，固定核对：
   - `reports/pipeline_report_latest.json`
   - `reports/train_report.json`
   - `reports/infer_report.json`
   - `manifests/hip_manifest.json`、`manifests/run_manifest.json`
