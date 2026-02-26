# docs 目录索引

> **快速导航** → [数据流总览](README.md#二数据流总览) · [模块介绍](README.md#三模块介绍) · [从 0 到 1 快速上手](README.md#五从-0-到-1快速上手)  
> 新手建议从 [README.md](README.md) 开始阅读，本文件为全量文件树索引。

---

## 1. 根目录文件

| 文件 | 说明 |
|------|------|
| [README.md](README.md) | **主导航入口**（数据流、模块介绍、Skill 使用、0-to-1 快速上手） |
| [INDEX.md](INDEX.md) | 本文件：全量文件树索引 |
| `ML Deformer 与 Groom 深度研究.pdf` | 配套 PDF 研究报告（离线阅读用） |

---

## 2. 分目录索引

### 2.1 `docs/01_theory` — 理论层

| 文件 | 说明 |
|------|------|
| [01_theory/README_MLDeformer_Groom_Theory_CN.md](01_theory/README_MLDeformer_Groom_Theory_CN.md) | LBS/DQS 基线 → NMM/NNM/Groom ML 残差变形范式；Houdini 求解器选择；实时部署关注点 |
| [01_theory/README_NMM_NNM_Groom_Compare_CN.md](01_theory/README_NMM_NNM_Groom_Compare_CN.md) | 三模型 6 维横向对比表；计算特征、内存特征、数据依赖、适用场景；首轮项目选型建议 |

### 2.2 `docs/02_code_map` — 源码映射层

| 文件 | 说明 |
|------|------|
| [02_code_map/README_UE5_CodeMap_Mainline_CN.md](02_code_map/README_UE5_CodeMap_Mainline_CN.md) | 一行主链路总览 + 三模型 5 个固定函数基准 + 跨层探针命令 |
| [02_code_map/README_UE5_Architecture_Diagram_CN.md](02_code_map/README_UE5_Architecture_Diagram_CN.md) | 5 张 Mermaid 架构图：总体分层、训练链时序、推理链时序、ComputeGraph Dispatch、Groom 写回 |
| [02_code_map/README_NMM_TheoryCode_CN.md](02_code_map/README_NMM_TheoryCode_CN.md) | NMM 理论↔UE 源码函数级映射；训练链、推理链、数据结构对照表；7 类失败模式 |
| [02_code_map/README_NNM_TheoryCode_CN.md](02_code_map/README_NNM_TheoryCode_CN.md) | NNM 理论↔源码映射；两阶段推理（网络 + `RunNearestNeighborModel`）；`OnPostTraining` 缓存失效 |
| [02_code_map/README_GroomDeformer_TheoryCode_CN.md](02_code_map/README_GroomDeformer_TheoryCode_CN.md) | Groom DataInterface 类族映射；HLSL 模板；RDG Dispatch 路径 |

#### 2.3 `docs/02_code_map/deep_dive` — Top-Down 7 层深度解析

| 文件 | 说明 |
|------|------|
| [02_code_map/deep_dive/README_UE5_TopDown_Source_Atlas_CN.md](02_code_map/deep_dive/README_UE5_TopDown_Source_Atlas_CN.md) | 7 层索引 + 跨层调用总图；各层线索表（线程上下文、数据载体、失败探针） |
| [02_code_map/deep_dive/README_L1_Module_Startup_CN.md](02_code_map/deep_dive/README_L1_Module_Startup_CN.md) | **L1** 四个模块 `StartupModule` 入口；`IMPLEMENT_MODULE` → 验证探针 |
| [02_code_map/deep_dive/README_L2_Editor_Train_CN.md](02_code_map/deep_dive/README_L2_Editor_Train_CN.md) | **L2** 完整训练链：Toolkit → EditorModel → TrainModel → LoadTrainedNetwork；4 类失败模式 |
| [02_code_map/deep_dive/README_L3_Runtime_Infer_CN.md](02_code_map/deep_dive/README_L3_Runtime_Infer_CN.md) | **L3** 推理链：Component::Tick → ModelInstance → SetupInputs/Execute → PostTick；4 个 STAT 探针 |
| [02_code_map/deep_dive/README_L4_Engine_MeshDeformer_CN.md](02_code_map/deep_dive/README_L4_Engine_MeshDeformer_CN.md) | **L4** SkinnedMeshComponent → EnqueueWork → MeshDeformer 分支；LOD 映射与输出缓冲区 |
| [02_code_map/deep_dive/README_L5_Optimus_ComputeGraph_CN.md](02_code_map/deep_dive/README_L5_Optimus_ComputeGraph_CN.md) | **L5** Optimus Compile → CreateOptimusInstance → EnqueueWork → Worker；Shader 编译阻塞路径 |
| [02_code_map/deep_dive/README_L6_DataInterface_Groom_CN.md](02_code_map/deep_dive/README_L6_DataInterface_Groom_CN.md) | **L6** 四个 Groom DataInterface 类；CreateDataProvider → AllocateResources → GatherDispatchData |
| [02_code_map/deep_dive/README_L7_Shader_RDG_Profiling_CN.md](02_code_map/deep_dive/README_L7_Shader_RDG_Profiling_CN.md) | **L7** HLSL `.ush` 模板映射；RDG 参数组装；5 个 Profiling 探针完整表 |

#### 2.4 `docs/02_code_map/core_line_by_line` — 核心文件逐行注释

| 文件 | 说明 |
|------|------|
| [02_code_map/core_line_by_line/README_Core_LineByLine_Index_CN.md](02_code_map/core_line_by_line/README_Core_LineByLine_Index_CN.md) | 逐行注释文件索引 + 字段定义 `line_range\|code_focus\|explanation\|breakpoint_probe` |
| [02_code_map/core_line_by_line/README_Core_01_MLDeformerComponent_CN.md](02_code_map/core_line_by_line/README_Core_01_MLDeformerComponent_CN.md) | `MLDeformerComponent.cpp`：构造 / Init / Tick 防护条件 / STAT 宏位置（12 关键段） |
| [02_code_map/core_line_by_line/README_Core_02_MLDeformerModelInstance_CN.md](02_code_map/core_line_by_line/README_Core_02_MLDeformerModelInstance_CN.md) | `ModelInstance`：骨骼 6-float 打包 / Curve AnimInstance 回退 / Tick 状态机 / 网格资产 ID 校验 |
| [02_code_map/core_line_by_line/README_Core_03_NeuralMorphModelInstance_CN.md](02_code_map/core_line_by_line/README_Core_03_NeuralMorphModelInstance_CN.md) | NMM：`SetupInputs` 维度检查 → `Execute` → Morph Weight 写回 + OOD Clamp |
| [02_code_map/core_line_by_line/README_Core_04_NearestNeighborModelInstance_CN.md](02_code_map/core_line_by_line/README_Core_04_NearestNeighborModelInstance_CN.md) | NNM：两阶段推理 + `DecayCoeff` + `PreviousWeights` 状态缓存 + `ClipInputs` |
| [02_code_map/core_line_by_line/README_Core_05_OptimusDeformerInstance_CN.md](02_code_map/core_line_by_line/README_Core_05_OptimusDeformerInstance_CN.md) | `SetupFromDeformer`：资源释放 → rebind → buffer pool → DataProvider 创建；`EnqueueWork` 执行组映射 |
| [02_code_map/core_line_by_line/README_Core_06_ComputeGraph_Dispatch_CN.md](02_code_map/core_line_by_line/README_Core_06_ComputeGraph_Dispatch_CN.md) | `ComputeGraphInstance`：DataProvider 创建 + Proxy 收集；`Worker`：核心提交 + `AddPass` 调度 |
| [02_code_map/core_line_by_line/README_Core_07_GroomWriteDataInterface_CN.md](02_code_map/core_line_by_line/README_Core_07_GroomWriteDataInterface_CN.md) | `DeformerDataInterfaceGroomWrite`：Pin 暴露 / `AllocateResources` 缓冲区掩码门控 / SRV/UAV 验证 |

### 2.5 `docs/03_dataset_pipeline` — 数据集制作

| 文件 | 说明 |
|------|------|
| [03_dataset_pipeline/README_Houdini_to_UE_Dataset_CN.md](03_dataset_pipeline/README_Houdini_to_UE_Dataset_CN.md) | 完整 5 步数据制作流程；**ABC 坐标双重变换陷阱**（Houdini + UE Maya preset = 两次翻转）及修复方案；9 点验收清单 |
| [03_dataset_pipeline/README_DataQC_Checklist_CN.md](03_dataset_pipeline/README_DataQC_Checklist_CN.md) | 8 类数据质量 Checklist（拓扑 / 时序 / ROM / 异常 / Delta / UE 预导入 / 训练后回归 / 记录模板） |

### 2.6 `docs/04_train_infer` — 训练与推理实操

| 文件 | 说明 |
|------|------|
| [04_train_infer/README_UE5_MLDeformer_TrainInfer_CN.md](04_train_infer/README_UE5_MLDeformer_TrainInfer_CN.md) | 训练前检查 → Editor 5 步训练链 → 加载 → 推理链；skip_train 模式；训练确定性治理（YAML seed 配置） |
| [04_train_infer/README_Profiling_And_Debug_CN.md](04_train_infer/README_Profiling_And_Debug_CN.md) | 核心性能指标 + 4 类失败诊断流程图（无变形 / 推理慢 / 极端姿势爆炸 / Groom 闪烁）；监控周期；问题报告模板 |

### 2.7 `docs/05_skill_analogy` — Skill 与类比

| 文件 | 说明 |
|------|------|
| [05_skill_analogy/README_Skill_Analogy_Matrix_CN.md](05_skill_analogy/README_Skill_Analogy_Matrix_CN.md) | 10 条工程主题 → 文档入口 → Skill → 触发场景 → 预期输出；5 个验证后新增失败模式 |
| [05_skill_analogy/README_Prototype_Skill_Summary_CN.md](05_skill_analogy/README_Prototype_Skill_Summary_CN.md) | 5 个 Skill 总结 + 3 个触发信号 + 4 个成功标准 + Rollback 模式 + 项目结束状态 |
| [05_skill_analogy/skill-ue5-mldeformer-train/SKILL.md](05_skill_analogy/skill-ue5-mldeformer-train/SKILL.md) | **Skill**：UE5 完整训练→推理→GT 对比；hou2ue_automation 流程；skip_train 快捷；坐标系验证；验证默认值 |
| [05_skill_analogy/skill-ue5-groom-deformer-debug/SKILL.md](05_skill_analogy/skill-ue5-groom-deformer-debug/SKILL.md) | **Skill**：Groom DataInterface 6 步 debug 流程；null group instance / 写回 buffer 无效 / binding 不匹配 |
| [05_skill_analogy/skill-prototype-data-acquisition/SKILL.md](05_skill_analogy/skill-prototype-data-acquisition/SKILL.md) | **Skill**：公开 + 门控数据集获取 4 步；输出 `assets_status.json` + `dataset_manifest.jsonl` |
| [05_skill_analogy/skill-prototype-wsl-train-orchestrator/SKILL.md](05_skill_analogy/skill-prototype-wsl-train-orchestrator/SKILL.md) | **Skill**：WSL NMM/NNM/Groom smoke 训练编排；输出 `train_report.json` × 3 + index |
| [05_skill_analogy/skill-prototype-win-infer-viz/SKILL.md](05_skill_analogy/skill-prototype-win-infer-viz/SKILL.md) | **Skill**：Windows 推理 + Jupyter 可视化；输出 `infer_report.json` × 3 + `pred_vs_gt.csv` |

### 2.8 `docs/06_appendix` — 附录

| 文件 | 说明 |
|------|------|
| [06_appendix/README_Source_References_CN.md](06_appendix/README_Source_References_CN.md) | UE5 源码 7 层符号索引（每层：文件绝对路径 + 关键符号 + `rg` 搜索命令）；防行号漂移维护策略 |

### 2.9 `docs/memory` — 进度检查点（归档用）

| 文件 | 说明 |
|------|------|
| [memory/checkpoint-20260225-skip-train-validated.md](memory/checkpoint-20260225-skip-train-validated.md) | 归档：训练非确定性根因 + ABC 坐标双重变换 bug 发现 + skip_train 方案验证 |
| [memory/checkpoint-20260225-unified-pipeline-validated.md](memory/checkpoint-20260225-unified-pipeline-validated.md) | 归档：windowed SSIM 方法论（11×11 uniform filter）+ coord 自动检测（Z-up 阈值） |
| [memory/checkpoint-20260226-full-validation-and-optimizations.md](memory/checkpoint-20260226-full-validation-and-optimizations.md) | **当前权威**：P1–P5 完整验证（full profile 46 帧 · 3× 稳定性 · skip_train shortcut · color GT · 下装 demo） |

---

## 3. 仓库根目录 `prototype/`（非 docs 目录 · 独立实现）

| 文件 | 说明 |
|------|------|
| [../prototype/README.md](../prototype/README.md) | 独立闭环设计约束 + 5 步快速上手 + 验证输出清单 |
| [../prototype/config/assets.manifest.yaml](../prototype/config/assets.manifest.yaml) | 6 个资产条目（3 公开 gltf + 3 门控/手动） |
| [../prototype/config/pipeline.defaults.yaml](../prototype/config/pipeline.defaults.yaml) | smoke 训练默认参数（GPU / max minutes / 推理延迟目标） |
| [../prototype/config/repos.lock.yaml](../prototype/config/repos.lock.yaml) | 6 个第三方仓库 Commit Pin（DeePSD / fast-snarf / neural-blend-shapes 等） |
| [../prototype/scripts/run_all.ps1](../prototype/scripts/run_all.ps1) | 一键编排：prep → data → train → infer → viz |
