# UE5 ML Deformer 文档总导航

## 0. 目录索引
- 目录树索引：`docs/INDEX.md`

## 1. 推荐阅读顺序
1. 理论总览：`docs/01_theory/README_MLDeformer_Groom_Theory_CN.md`
2. 主链路导航：`docs/02_code_map/README_UE5_CodeMap_Mainline_CN.md`
3. 架构图文：`docs/02_code_map/README_UE5_Architecture_Diagram_CN.md`
4. 分层深度：`docs/02_code_map/deep_dive/README_UE5_TopDown_Source_Atlas_CN.md`
5. 核心逐行：`docs/02_code_map/core_line_by_line/README_Core_LineByLine_Index_CN.md`
6. 实操文档：数据管线 + 训练推理 + 调试
7. 原型闭环：`prototype/README.md`

## 2. 分层入口

### 理论层
- `docs/01_theory/README_MLDeformer_Groom_Theory_CN.md`
- `docs/01_theory/README_NMM_NNM_Groom_Compare_CN.md`

### 源码映射层
- `docs/02_code_map/README_UE5_CodeMap_Mainline_CN.md`
- `docs/02_code_map/README_UE5_Architecture_Diagram_CN.md`
- `docs/02_code_map/README_NMM_TheoryCode_CN.md`
- `docs/02_code_map/README_NNM_TheoryCode_CN.md`
- `docs/02_code_map/README_GroomDeformer_TheoryCode_CN.md`

### 深度解析层（Top-Down 7层）
- `docs/02_code_map/deep_dive/README_UE5_TopDown_Source_Atlas_CN.md`
- `docs/02_code_map/deep_dive/README_L1_Module_Startup_CN.md`
- `docs/02_code_map/deep_dive/README_L2_Editor_Train_CN.md`
- `docs/02_code_map/deep_dive/README_L3_Runtime_Infer_CN.md`
- `docs/02_code_map/deep_dive/README_L4_Engine_MeshDeformer_CN.md`
- `docs/02_code_map/deep_dive/README_L5_Optimus_ComputeGraph_CN.md`
- `docs/02_code_map/deep_dive/README_L6_DataInterface_Groom_CN.md`
- `docs/02_code_map/deep_dive/README_L7_Shader_RDG_Profiling_CN.md`

### 深度解析层（逐行核心代码）
- `docs/02_code_map/core_line_by_line/README_Core_LineByLine_Index_CN.md`
- `docs/02_code_map/core_line_by_line/README_Core_01_MLDeformerComponent_CN.md`
- `docs/02_code_map/core_line_by_line/README_Core_02_MLDeformerModelInstance_CN.md`
- `docs/02_code_map/core_line_by_line/README_Core_03_NeuralMorphModelInstance_CN.md`
- `docs/02_code_map/core_line_by_line/README_Core_04_NearestNeighborModelInstance_CN.md`
- `docs/02_code_map/core_line_by_line/README_Core_05_OptimusDeformerInstance_CN.md`
- `docs/02_code_map/core_line_by_line/README_Core_06_ComputeGraph_Dispatch_CN.md`
- `docs/02_code_map/core_line_by_line/README_Core_07_GroomWriteDataInterface_CN.md`

### 数据与实操层
- `docs/03_dataset_pipeline/README_Houdini_to_UE_Dataset_CN.md`
- `docs/03_dataset_pipeline/README_DataQC_Checklist_CN.md`
- `docs/04_train_infer/README_UE5_MLDeformer_TrainInfer_CN.md`
- `docs/04_train_infer/README_Profiling_And_Debug_CN.md`

### Prototype 层（WSL 训练 + Windows 推理）
- `prototype/README.md`
- `prototype/config/repos.lock.yaml`
- `prototype/config/assets.manifest.yaml`
- `prototype/scripts/run_all.ps1`

### Skill 与附录层
- `docs/05_skill_analogy/README_Skill_Analogy_Matrix_CN.md`
- `docs/05_skill_analogy/README_Prototype_Skill_Summary_CN.md`
- `docs/05_skill_analogy/skill-ue5-mldeformer-train/SKILL.md`
- `docs/05_skill_analogy/skill-ue5-groom-deformer-debug/SKILL.md`
- `docs/05_skill_analogy/skill-prototype-data-acquisition/SKILL.md`
- `docs/05_skill_analogy/skill-prototype-wsl-train-orchestrator/SKILL.md`
- `docs/05_skill_analogy/skill-prototype-win-infer-viz/SKILL.md`
- `docs/06_appendix/README_Source_References_CN.md`

## 3. 变更说明
- `docs/references` 已移除。
- 新增 `prototype/` 用于跨平台最小闭环验证。

## 4. 字段约定
1. 映射字段：`concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation`
2. 分层字段：`layer | parent_symbol | child_symbol | file_path | thread_context | data_carrier | failure_point | probe`
3. 逐行字段：`line_range | code_focus | explanation | breakpoint_probe`
4. 技能字段：`name | description | trigger | prerequisites | steps | outputs | failure_modes | verification`
