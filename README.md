# MLDeformerSample 学习与工程仓库

本仓库用于系统化学习 UE5 `ML Deformer` 与 `Groom Deformer`，并沉淀一套可复用的理论-源码-数据-训练推理文档体系。

## 快速入口
- 文档总导航：`docs/README.md`
- Unreal 项目：`MLDeformerSample.uproject`
- 参考资料（复用，不改动）：`docs/references/docs/README.md`

## 当前目标范围（首轮）
- UE 版本：`5.5`
- 模型范围：`Neural Morph Model (NMM)`、`Nearest Neighbor Model (NNM)`、`Groom Deformer`
- 交付形式：纯 Markdown 文档体系 + 本地 Git 仓库规范化

## 仓库规范
- 已启用 Git LFS 跟踪 Unreal 二进制资源（见 `.gitattributes`）
- Unreal 构建产物与缓存目录已通过 `.gitignore` 忽略

## 文档结构
- `docs/01_theory/`：理论重构与模型对比
- `docs/02_code_map/`：UE5 源码链路与理论映射
- `docs/03_dataset_pipeline/`：Houdini -> UE 数据集制作
- `docs/04_train_infer/`：训练、推理、性能与排障
- `docs/05_skill_analogy/`：skill 类比矩阵与 UE 专用 skill 草案
- `docs/06_appendix/`：源码与资料索引
