# UE5 ML Deformer 与 Groom 文档系统（中文）

## 0. 使用方式
1. 先读 `docs/01_theory/README_MLDeformer_Groom_Theory_CN.md` 建立整体理论框架。
2. 再读 `docs/02_code_map/README_UE5_CodeMap_Mainline_CN.md` 对齐 UE5 训练/推理源码主链。
3. 接着按模型阅读映射文档（NMM / NNM / Groom）。
4. 实操时配合数据管线与训练推理指南。

## 1. 理论层
- `docs/01_theory/README_MLDeformer_Groom_Theory_CN.md`
- `docs/01_theory/README_NMM_NNM_Groom_Compare_CN.md`

## 2. 源码映射层
- `docs/02_code_map/README_UE5_CodeMap_Mainline_CN.md`
- `docs/02_code_map/README_NMM_TheoryCode_CN.md`
- `docs/02_code_map/README_NNM_TheoryCode_CN.md`
- `docs/02_code_map/README_GroomDeformer_TheoryCode_CN.md`

## 3. 数据管线层
- `docs/03_dataset_pipeline/README_Houdini_to_UE_Dataset_CN.md`
- `docs/03_dataset_pipeline/README_DataQC_Checklist_CN.md`

## 4. 训练与推理层
- `docs/04_train_infer/README_UE5_MLDeformer_TrainInfer_CN.md`
- `docs/04_train_infer/README_Profiling_And_Debug_CN.md`

## 5. Skill 类比与草案
- `docs/05_skill_analogy/README_Skill_Analogy_Matrix_CN.md`
- `docs/05_skill_analogy/skill-ue5-mldeformer-train/SKILL.md`
- `docs/05_skill_analogy/skill-ue5-groom-deformer-debug/SKILL.md`

## 6. 附录
- `docs/06_appendix/README_Source_References_CN.md`

## 7. 参考资料（仅链接复用，不改动）
- `docs/references/docs/README.md`
- `docs/references/docs/guides/README_LearningPlan.md`
- `docs/references/docs/paper/README.md`
- `docs/references/docs/paper_code/README.md`

## 8. 文档接口约定
映射文档统一字段：
`concept | paper_ref | ue_module | file_path | symbol | train_or_infer | explanation | validation`

Skill 文档统一结构：
`name | description | trigger | prerequisites | steps | outputs | failure_modes | verification`
