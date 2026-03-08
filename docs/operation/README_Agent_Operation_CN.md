# Agent 操作手册：如何定位 Houdini / UE 场景、串联双软件并调试

> **用途**：回答“agent 是怎么知道 HIP / UE 场景信息的”“怎么把 Houdini 和 UE 串起来”“实际排障依据是什么”。  
> **对应实践来源**：`docs/05_skill_analogy/skill-ue5-mldeformer-train/SKILL.md` + `pipeline/hou2ue/` 实际脚本 + `Source/MLDeformerSampleEditorTools/` C++ bridge。

---

## 1. 先说结论：agent 不是“直接读懂二进制 hip/uasset”

本项目里的 agent 并不是靠“裸解析” `.hip`、`.uasset`、`.umap` 这类二进制文件来理解场景。

它真正依赖的是 4 类可编程接口：

1. **Houdini Python API（`hou`）**：用 `hython` 打开 `.hip`，按节点路径读取 node / parm / PDG 结构。
2. **UE Python API（`unreal`）**：在 Unreal Editor / UnrealEditor-Cmd 进程内读取 asset、LevelSequence、MoviePipeline、GeometryCache 等信息。
3. **UE C++ bridge（`UMLDTrainAutomationLibrary`）**：把训练、配置、dump 这些 Unreal Python 难以稳定访问的编辑器能力，封装成 `BlueprintCallable` 接口给 Python 调用。
4. **流水线清单与阶段报告**：所有阶段都会把“发现了什么、生成了什么、失败在哪里”写成 JSON，agent 实际上是通过这些结构化产物建立对场景和流程的理解。

因此，agent 对场景的“理解”不是一次性读文件完成的，而是：

`配置 -> 运行宿主 API -> 生成 manifest/report -> 再根据 manifest/report 做下一步判断`

---

## 2. 这份文档和 Skill 的关系

`docs/05_skill_analogy/skill-ue5-mldeformer-train/SKILL.md` 给的是**操作策略层**：

- 什么时候该训练
- 什么时候该 strict clone
- 什么时候该做 GT compare
- 遇到什么失败模式先查什么

而本文件给的是**实现层**：

- 这些动作在代码里由谁执行
- 场景信息从哪里读出来
- 两个软件之间靠什么传参和对接
- agent 调试时到底看哪些文件和哪些信号

可以把它理解为：

- `SKILL.md` 解决“该怎么做”
- `docs/operation/README_Agent_Operation_CN.md` 解决“agent 实际怎么做到”

---

## 3. agent 如何知道 Houdini 里的场景信息

### 3.1 不是扫整个 HIP，而是按配置中的关键节点路径定向读取

脚本入口是 `pipeline/hou2ue/scripts/parse_hip.py`。

它做的事情非常具体：

1. 读取管线配置里的 `paths.hip_file`；
2. 用 `import hou` + `hou.hipFile.load(...)` 打开 HIP；
3. 从 `houdini.nodes` 里取关键节点路径；
4. 用 `_require_node()` / `_require_parm()` 强制确认这些节点和参数存在；
5. 把结果写成 `manifests/hip_manifest.json`。

它当前明确读取的内容包括：

- `pose_range` 节点上的 `intvalue1_*` 姿态帧列表
- `local_scheduler.maxprocs`
- `pdg_anim_input.fbxfile`
- `*_mesh.sopoutput` 这类 PDG 输出路径

也就是说，agent 不是“猜 HIP 里可能有什么”，而是依赖：

- 项目配置中声明的节点路径
- Houdini API 实际返回的 node / parm
- 最终落盘的 `hip_manifest.json`

### 3.2 HIP 里的“场景结构”最后会被压缩成 manifest

`parse_hip.py` 输出的 manifest 里会记录：

- HIP 文件路径
- Houdini 版本
- 关键输入参数
- pose 数量与帧索引
- PDG mesh 输出节点列表

所以后续 agent 不需要每次重新打开 HIP 才知道结构，只要读取：

- `manifests/hip_manifest.json`
- `resolved_config.yaml`
- `reports/preflight_report.json`

就能知道当前这轮运行期望使用什么 Houdini 场景结构。

### 3.3 Houdini 导出阶段不仅导文件，还顺便验证坐标系

`pipeline/hou2ue/scripts/houdini_export_abc.py` 不只是“导出 Alembic”。它还做了两件对 agent 很关键的事：

1. **显式坐标变换**：读取 `houdini.coord_system`，决定 `scale_factor`、`matrix_3x3`、`translation_offset`；
2. **bbox 证据输出**：通过 hython 构造临时 SOP 链，导出前后都取 bbox，并把结果写进坐标校验 payload。

这个脚本里还能自动检测 up-axis：

- 如果 Z 向中心更显著，认为是 `z_up`
- 如果 Y 向中心更显著，认为是 `y_up`

所以 agent 后面判断“是不是坐标错了”，不是凭画面猜，而是看：

- `coord_validation_manifest.json`
- 导入后 bbox 与导出前 bbox 是否成比例匹配
- 阶段报告里有没有 tolerance mismatch

---

## 4. agent 如何知道 UE 里的场景和资产信息

### 4.1 UE Python 阶段统一通过环境变量拿上下文

UE 侧所有 Python 脚本共享 `pipeline/hou2ue/scripts/ue_common.py`。

它不是直接读当前编辑器状态，而是先从环境变量取运行上下文：

- `HOU2UE_CONFIG`
- `HOU2UE_RUN_DIR`
- `HOU2UE_PROFILE`

然后解析配置，得到当前 run 的统一语境。

这意味着 agent 在 UE 里不是“手点编辑器看场景”，而是通过：

- 当前配置
- 当前 run_dir
- 当前阶段脚本

来约束自己应该观察哪些资产和哪些场景。

### 4.2 UE Import 阶段知道的不是“地图信息”，而是 asset 图谱

`pipeline/hou2ue/scripts/ue_import.py` 负责把 FBX / ABC 导入 UE，并读取或校验：

- 目标 asset path 是否存在
- 导入后对象路径
- Geometry Cache 的 bounds
- Alembic 导入设置（尤其是 `CUSTOM` conversion preset）

它会显式关闭 UE 默认的 Maya 坐标转换：

- `AbcConversionPreset.CUSTOM`
- `rotation = (0,0,0)`
- `scale = (1,1,1)`

所以 agent 判断“为什么 UE 导入后形变变坏了”，首先不是去看 `.uasset` 二进制，而是先看：

- `ue_import_report.json`
- `coord_validation_report.json`
- 导入后 Geometry Cache 的 bbox 是否异常

### 4.3 UE 训练配置读取靠 C++ bridge，不靠脆弱反射

最核心的定位能力来自 `Source/MLDeformerSampleEditorTools/`。

这里定义了 `UMLDTrainAutomationLibrary`，提供 4 个 `BlueprintCallable` 接口：

- `TrainDeformerAsset`
- `EnsureModelType`
- `SetupDeformerAsset`
- `DumpDeformerSetup`

对应的 request/result 结构在 `Public/MLDTrainTypes.h` 里，包含：

- `FMldTrainRequest`
- `FMldSetupRequest`
- `FMldDumpRequest`

为什么这很关键：

因为 Unreal Python 对 ML Deformer 编辑器内部很多状态访问并不稳定，单纯 `unreal.load_asset()` 只能拿到资产壳，拿不到完整的 editor model 语义。这个 bridge 让 Python 可以可靠地做三件事：

1. **配置资产**：把 skeletal mesh / graph / test anim / training inputs / model overrides 写进去；
2. **导出资产结构**：把当前 deformer 配置 dump 成 JSON；
3. **触发训练并取回结果**：包括返回码、耗时、网络加载状态。

### 4.4 agent 是怎么知道训练资产“长什么样”的

答案是：通过 `DumpDeformerSetup`。

`pipeline/hou2ue/scripts/ue_dump_setup.py` 和 `dump_reference_setup.py` 会在 UE 进程里调用这个接口，把以下信息导出成 JSON：

- model type
- skeletal mesh
- deformer graph
- test animation
- training input anims
- NNM sections
- model overrides

这就是 strict clone / setup diff 的基础。

换句话说，agent 并不是“直接读 uasset 得到训练配置”，而是：

`uasset -> UE editor model -> C++ bridge -> JSON dump`

这个 JSON dump 才是 agent 后续比较 source / reference 差异的依据。

---

## 5. agent 如何知道运行时场景和序列信息

### 5.1 Demo/GT 捕获不是“看地图”，而是由 MoviePipeline 执行器读取命令行

运行时采集由 `Content/Python/Hou2UeDemoRuntimeExecutor.py` 完成。

它会从命令行参数里读取：

- `DemoSequence`
- `DemoAnim`
- `DemoOutputDir`
- `DemoReportJson`
- `DemoMap`
- `DemoStartFrame`
- `DemoEndFrame`
- `DemoWarmupFrames`
- 分辨率等参数

因此 agent 知道“当前采的是哪个场景、哪个序列、哪段帧范围”，依赖的不是人工口述，而是由外层脚本明确传参。

### 5.2 它还会直接检查 LevelSequence 里有没有动画轨

这个执行器内部会遍历 bindings / tracks / sections，寻找 `MovieSceneSkeletalAnimationTrack`，并把目标动画替换到对应 section。

所以 agent 能判断：

- 为什么某个 sequence 不能用来做 demo
- 为什么动画没有替换成功
- 为什么只渲了 camera 没渲到角色

判断依据是：

- 是否找到 skeletal animation track
- 是否成功替换 section 的 animation
- 最终 `demo_report.json` 是否写出成功

这也解释了 Skill 里那条经验：

> `Main_Sequence` 等 cinematic 序列如果没有 `MovieSceneSkeletalAnimationTrack`，就不能直接当 demo 采集入口。

---

## 6. agent 如何把 Houdini 和 UE 串起来

### 6.1 串联器就是 `pipeline/hou2ue/run_all.ps1`

主编排脚本是 `pipeline/hou2ue/run_all.ps1`。它定义了完整 stage 顺序：

`baseline_sync -> preflight -> houdini -> convert -> ue_import -> ue_setup -> train -> infer -> gt_reference_capture -> gt_source_capture -> gt_compare -> report`

它做的核心工作不是算法本身，而是：

1. 解析 `-Stage / -Profile / -Config / -RunDir`
2. 为每一阶段选择正确解释器：`python`、`hython`、`UnrealEditor-Cmd`
3. 用 guard 包装进程，检测：
   - 超时
   - 长时间无活动
   - 重复报错行
4. 统一把 stdout / stderr / 阶段 report 放到 `run_dir/reports/`

所以 agent 实际串联双软件，不是手工“先开 Houdini 再开 UE”，而是依赖编排脚本确保：

- 输入路径一致
- profile 一致
- run_dir 一致
- 每阶段产物落在固定位置

### 6.2 跨进程靠“配置 + 环境变量 + report”传递上下文

跨 Houdini / UE 进程传递上下文有三条通道：

1. **配置文件**：`pipeline.yaml` / `pipeline.full_exec.yaml`
2. **环境变量**：尤其是 UE Python 读取的 `HOU2UE_*`
3. **阶段产物**：`manifests/*.json`、`reports/*_report.json`

这让 agent 可以做到：

- 上一阶段结束后，不靠内存记忆，而是靠 report 继续下一阶段
- 某一阶段崩了以后，可以从 `RunDir` 断点续跑
- source/reference/worktree 之间可以做结构 diff

### 6.3 为什么这套方式适合 agent 调试

因为它天然可追溯。

agent 每次排障都可以回答三个问题：

1. **当时想做什么**：看 `resolved_config.yaml`
2. **实际做了什么**：看某个 stage 的 `*_report.json`
3. **产出了什么**：看 `manifests/`、`workspace/staging/`、训练文件和图片序列

---

## 7. agent 调试时具体看什么

### 7.1 第一层：看阶段报告，而不是先看大日志

优先级最高的是：

- `reports/preflight_report.json`
- `reports/convert_report.json`
- `reports/ue_import_report.json`
- `reports/ue_setup_report.json`
- `reports/train_report.json`
- `reports/infer_report.json`
- `reports/gt_compare_report.json`
- `reports/pipeline_report_latest.json`

原因很简单：这些报告已经把“阶段状态、输入、输出、错误”结构化了，比几万行 editor log 更适合 agent 快速定位。

### 7.2 第二层：看 manifest，确认“理解的场景”是否正确

关键 manifest 包括：

- `manifests/hip_manifest.json`
- `manifests/run_manifest.json`
- `manifests/coord_validation_manifest.json`

它们分别回答：

- Houdini 场景节点和参数是不是我以为的那套
- 这轮 run 选用了哪些输入文件
- 坐标/尺度校验是不是已经偏掉了

### 7.3 第三层：才看宿主日志

当 report 只能告诉你“失败了”但说不清为什么时，再下钻：

- Houdini / python guard stdout/stderr
- UE `Saved/Logs/MLDeformerSample.log`
- `reports/logs/gt_*`

`run_all.ps1` 的 guard 机制本身也会在超时、无活动、重复报错时给出 stderr tail，这对 agent 特别有用。

### 7.4 第四层：看视觉证据和指标证据

`compare_groundtruth.py` 提供的不是单一 pass/fail，而是一组可定位证据：

- SSIM
- PSNR
- Edge IoU
- worst frame
- 热力图

所以 agent 能把“感觉不对”落成：

- 是全局都差，还是某几个 shot 特别差
- 是结构错了，还是颜色漂了
- 是 OOD 姿态，还是坐标/单位已经坏了

---

## 8. 典型定位路径

### 8.1 为什么 agent 能定位 smoke GC 单位错误

定位链路不是“看画面觉得黑”，而是：

1. `gt_compare_report.json` 显示 ssim 大幅下降；
2. source frames 某些 shot 接近 near-black；
3. `outputs.bin` 统计显示顶点位移 p50=90.7 cm；
4. 回溯到 Houdini → ABC 链路，发现坐标/单位有误。

### 8.2 为什么 agent 能定位 NMM Local / Global 根因

定位链路也不是“试出来的”，而是：

1. `DumpDeformerSetup` 导出 reference 的 model_overrides；
2. `ue_setup_assets.py` 的 diff 机制比较 current / reference 配置；
3. 训练产物尺寸远大于 reference（1680 MB vs 306 MB）；
4. 结合 `MLDTrainAutomationLibrary` 训练结果与 model type / overrides，确认默认 Local 导致过参数化。

### 8.3 为什么 agent 能定位“场景没接上”而不是“训练坏了”

如果 `Hou2UeDemoRuntimeExecutor` 找不到 `MovieSceneSkeletalAnimationTrack`，或动画 section 没替换成功，那么这类问题属于：

- 场景/序列接线错误
- 运行时捕获入口错误

而不是训练失败。

这就是为什么 operation 文档必须把“资产配置问题”和“场景接线问题”分开讲。

---

## 9. agent 的工作边界

这套方法很强，但也有边界：

1. **不会魔法解析任意 hip**：必须有配置里声明的关键节点路径，或至少有明确的 PDG 输出约定。
2. **不会直接理解任意 uasset 二进制**：必须通过 UE Python / C++ bridge 导出结构化信息。
3. **不会把 report 缺失当成功**：本项目很多阶段都以 `*_report.json.status` 为准，而不是只看进程退出码。
4. **不会把所有视觉异常都归因于训练**：还要先排除导入、场景、序列、渲染捕获、GPU 稳定性等链路问题。

---

## 10. 给未来 agent / 维护者的操作建议

1. 新增 Houdini 场景变体时，优先先扩展 `parse_hip.py` 的 manifest 字段，而不是直接把判断逻辑写死在对话里。
2. 新增 UE 训练参数时，优先扩展 `FMldSetupRequest` / `FMldDumpResult`，保持“可配置”和“可回读”成对出现。
3. 每增加一个关键阶段，都要产出结构化 report；否则 agent 只能回退到低效的大日志排查。
4. 当一个问题可以通过 manifest / diff / metrics 证明时，不要只用截图描述。

---

## 11. 快速索引

| 目标 | 入口 |
|------|------|
| 看操作策略 | `docs/05_skill_analogy/skill-ue5-mldeformer-train/SKILL.md` |
| 看 Houdini 场景解析 | `pipeline/hou2ue/scripts/parse_hip.py` |
| 看 Alembic 导出与坐标修正 | `pipeline/hou2ue/scripts/houdini_export_abc.py` |
| 看 UE 导入与坐标校验 | `pipeline/hou2ue/scripts/ue_import.py` |
| 看 UE 资产配置 | `pipeline/hou2ue/scripts/ue_setup_assets.py` |
| 看 UE 训练触发 | `pipeline/hou2ue/scripts/ue_train.py` |
| 看统一编排 | `pipeline/hou2ue/run_all.ps1` |
| 看 UE C++ bridge | `Source/MLDeformerSampleEditorTools/Public/MLDTrainAutomationLibrary.h` |
| 看 request/result 结构 | `Source/MLDeformerSampleEditorTools/Public/MLDTrainTypes.h` |
| 看运行时渲染执行器 | `Content/Python/Hou2UeDemoRuntimeExecutor.py` |
