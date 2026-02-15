# 核心代码逐行解析索引（Core Line-by-Line）

> 目录位置：`docs/02_code_map/core_line_by_line`（与 `deep_dive` 同级）
> 
> 目标：对核心运行链路做“按代码行号”的深度解析，便于源码阅读与断点调试。

## 1. 阅读顺序
1. `README_Core_01_MLDeformerComponent_CN.md`
2. `README_Core_02_MLDeformerModelInstance_CN.md`
3. `README_Core_03_NeuralMorphModelInstance_CN.md`
4. `README_Core_04_NearestNeighborModelInstance_CN.md`
5. `README_Core_05_OptimusDeformerInstance_CN.md`
6. `README_Core_06_ComputeGraph_Dispatch_CN.md`
7. `README_Core_07_GroomWriteDataInterface_CN.md`

## 2. 文档约定
1. 每篇包含“关键行段解析表”：`line_range | code_focus | explanation | breakpoint_probe`。
2. 行号基线固定：`UE_ROOT = D:/UE/UnrealEngine`，`EngineAssociation = 5.5`。
3. 优先解释控制流、边界条件、失败分支、线程切换与数据载体。

## 3. 与其它目录关系
1. `deep_dive/`：讲分层架构与跨模块链路。
2. `core_line_by_line/`：讲单文件内的关键实现细节。
3. 模型专题（NMM/NNM/Groom）用于理论-实现映射，不替代逐行阅读。

## 4. 快速跳转
- 主链路总线：`docs/02_code_map/README_UE5_CodeMap_Mainline_CN.md`
- 架构图文档：`docs/02_code_map/README_UE5_Architecture_Diagram_CN.md`
