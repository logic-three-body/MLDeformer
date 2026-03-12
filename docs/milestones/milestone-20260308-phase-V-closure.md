# 里程碑：Phase V 闭环 — NMM Global 模式 128 形态目标 PASS

**日期：** 2026-03-08  
**状态：** ✅ 闭环达成  
**最终指标：** ssim_mean = **0.8999**（阈值 ≥ 0.83），9 项指标全部通过

> **2026-03-12 更新说明**：本文档保留的是 Phase V 当时在 UE5.7 分支上的历史闭环结论，不应再被解读为“Global 是跨版本唯一正确答案”。最新验证见 [milestone-20260312-reference-local-vs-global-5.5.md](milestone-20260312-reference-local-vs-global-5.5.md)：在 `Refference + UE5.5` 中，`Local` 与 `Global` 都健康，且关键 Houdini 训练资产在 `Refference/` 与 `UE57/` 两边已验证一致。当前目标已转为定位 UE5.7 Neural Morph 实现/运行时差异。

---

## 一、执行摘要

经过从 2026-02-01 到 2026-03-08 的完整排查周期，  
最终将 NMM（Neural Morph Model）从默认 **Local 模式**切换为 **Global 模式（128 形态目标）**，  
训练产出 207 MB 模型，在 1560 帧完整 Main_Sequence 上实现 ssim = 0.8999，  
全面通过 9 项质量阈值，与 Epic Refference（0.9142）的差距缩小至 1.5 个百分点。

需要特别说明的是：**UE5.7 一开始出问题，并不是因为“UE5.7 引擎本身不可用”**，而是因为项目在从 UE5.5 / Epic Refference 迁移到 UE5.7 自训练链路时，先后偏离了参考工程的几个关键前提：

> **术语说明**：本里程碑中的 `Refference` / `Reference` 有时指 `Refference/` 只读工程，有时指从该工程复制出的 Epic 预训练资产或 GT 对比基线。若未显式写成 `Refference/` 目录路径，下文优先按“参考资产 / 参考基线”理解，而不是默认等同于“已直接读取并确认过其原始工程配置”。

1. **训练环境不可完全复现 UE5.5 参考权重**：跨 GPU / CUDA / cuDNN / PyTorch 栈重训存在非确定性，同配置不保证得到与 Refference 完全一致的权重；
2. **Houdini → UE 数据链路早期存在坐标/单位问题**：ABC 导入一度存在双重坐标变换风险，后续又确认 smoke GC 存在单位换算错误，直接污染训练数据；
3. **NMM 架构配置未对齐参考基线**：UE 默认 `Local` 模式被沿用到 UE5.7 训练，而现有尺寸与效果证据更支持 Epic 参考资产接近 `Global` 128 morph targets，而非默认 `Local`；这才是最终导致 1680 MB 过大模型和 ssim≈0.66 的主根因之一。该判断主要来自尺寸、指标与 setup diff 的综合反推，不应表述成“已直接读取 Refference 原始工程并唯一确认”。

因此，Phase V 的意义应理解为：在当时那条 UE5.7 排障支线上，`Global 128` 是一个有效恢复路径。最新文档应再叠加一层边界：它解释了那条支线为何能通过，但不再单独构成“5.5 → 5.7 根因已唯一锁定”的证明。

---

## 二、为什么 UE5.7 一开始会出问题

如果只问一句“为什么 UE5.7 一开始会出问题”，最准确的回答是：

> **项目最初把 UE5.5 / Epic Refference 的结果当成了可在 UE5.7 上直接重训复现的基线，但实际上训练确定性、GeomCache 数据质量和 NMM 模式配置三件事都没有被完整对齐。**

按因果顺序看，早期问题可以分为三层：

| 层级 | 早期表现 | 实际原因 | 后续修复 |
|------|----------|----------|----------|
| 训练复现层 | 相同流程重跑后，指标无法稳定贴近 Refference | 跨硬件 / CUDA / cuDNN / PyTorch 的训练非确定性，导致权重不能 bit-exact 对齐 | 引入 `skip_train` 基线、区分“参考资产一致性”与“自训练质量” |
| 数据链路层 | 新训练模型出现 near-black 帧、形变失真、2 GB 异常膨胀 | Houdini → UE 的 ABC / GeomCache 链路存在坐标与单位问题；smoke GC 顶点位移 p50 达 90.7 cm | 改用已验证的 PDG 原始 5kGreedyROM，并补充 QC 思路 |
| 架构配置层 | 即便换回正常 GC，模型仍 1680 MB 且 ssim≈0.660 | UE5.7 训练沿用了 NMM 默认 `Local` 模式，而不是与 Refference 参考资产量级和效果更一致的 `Global` 128 配置 | 在 `pipeline.full_exec.yaml` 中显式切到 `mode: global` + `global_num_morph_targets: 128` |

换句话说，**UE5.7 一开始的“问题”本质上是迁移偏航**：
不是单一 bug，而是“参考权重不可直接重训复现 + 训练数据链路一度有误 + 模型模式没有对齐参考架构”三者叠加。

---

## 三、完整问题解决时间线

### 2026-02-01 — 基线建立

| 项目 | 详情 |
|------|------|
| 模型 | Epic Refference 预训练 NMM，306 MB |
| 来源 | `Refference/Content/Characters/Emil/Deformers/MLD_NMMl_flesh_upperBody.uasset` |
| 测试结果 | ssim_mean = **0.9142** ✅ |
| 意义 | 建立了本项目所有实验的参照基准 |

---

### 2026-03-01 — 管线建立 + LBS 基线确认

| 项目 | 详情 |
|------|------|
| 事件 | `pipeline/hou2ue/run_all.ps1` 端到端管线首次全流程通过 |
| 测试模式 | LBS-vs-MLD 对比（source=MLD激活，reference=LBS only） |
| 结果 | ssim_mean = 0.5904 |
| 说明 | **这是正常的**：LBS 姿势与 MLD 激活图像本身有差异，0.59 是预期的"有差异"基线，不是失败 |
| 关键修复 | `MLDeformer.ForceWeight 0` CVar 替代 `set_active(False)`（后者会导致 GPU TDR 崩溃） |

> 这一阶段还说明了一个容易误判的问题：早期很多“UE5.7 不对”的现象，实际上是**测量口径还没和 UE5.5 参考工程分离清楚**。LBS-vs-MLD 的 0.59 不能直接解读为训练失败，它只是说明 source/reference 本来就不是同一画面语义。

---

### 2026-03-03 — 第一次 NMM 训练失败（smoke GC 几何质量问题）

| 项目 | 详情 |
|------|------|
| 训练数据 | `GC_upperBodyFlesh_smoke`（1.65 GB，pipeline 自动生成） |
| 训练结果 | 模型从 306 MB **膨胀至 2 GB**，outputs.bin = 1.34 GB |
| 推理表现 | shots 5-6（frames 1231-1428）出现**近黑色帧**（src_mean ≈ 16，ref_mean ≈ 77） |
| ssim 结果 | ssim_mean = **0.5904**（与 LBS 基线相同 → 模型输出无效） |
| **根因** | Houdini → UE ABC 导出时**单位换算错误**：顶点偏移 p50_max = **90.7 cm**（正常范围 5–30 cm）。极端顶点位移导致背面剔除（backface culling），产生近黑色帧 |

**教训**：GC 导出前必须检查 `outputs.bin` 顶点偏移分布；p50_max > 30 cm 应视为红旗。

---

### 2026-03-05 Phase TI — 调查确认 smoke GC 有害

通过对 `Intermediate/NeuralMorphModel/outputs.bin` 的统计分析：

```
Per-frame max-abs vertex offset distribution:
  p50 = 90.7 cm  → 超出物理合理范围
  p90 = 119.7 cm
  max = 148.7 cm（frame 714）
  35% 帧的最大顶点位移 > 100 cm
```

**结论**：smoke GC 数据集有害，需要从已验证的 PDG 原始数据重建。

---

### 2026-03-05 Phase T v3 — 还原 Refference 306 MB 模型（基线恢复）

| 操作 | 详情 |
|------|------|
| 操作 | 从 `Refference/` 复制 306 MB 预训练模型，覆盖 2 GB 损坏模型 |
| 结果 | ssim_mean = **0.9142** ✅（与 2026-02-01 基线完全一致） |
| 意义 | 证明管线本身没有问题，问题仅在训练数据质量 |
| per-window | F0-99: 0.9784，F500-599: 0.8206（最低，NMM 对极端姿态推理精度有限） |

---

### 2026-03-05 Phase T v4 — hero64 GC 训练（姿态覆盖不足，OOD 失败）

| 项目 | 详情 |
|------|------|
| 训练数据 | `GC_upperBodyFlesh_hero64`（117 MB，几何质量正常：p50_max = 4.0 cm ✅） |
| 训练结果 | 357 MB 模型，loss = 0.021（25k iter） |
| 推理表现 | ssim_mean = **0.637** ❌ |
| **根因** | hero64 仅 5065 帧，pose 分布覆盖面窄；Main_Sequence 包含 hero64 训练集中**未出现的姿态（OOD）**，模型在 OOD 条件下产生错误形变 |

**教训**：训练数据的 pose 分布必须覆盖推理时的 pose 空间；小数据集（hero64）不足以替代完整 ROM（5k Greedy ROM）。

---

### 2026-03-07 Phase U — 5kGreedyROM GC + Local 模式（过参数化失败）

| 项目 | 详情 |
|------|------|
| 训练数据 | `GC_upperBodyFlesh_5kGreedyROM`（8.46 GB，PDG 原始 Feb 2 🟢 几何正常） |
| 训练模式 | **Local**（UE 默认） |
| 训练结果 | **1680 MB** 模型（Epic Refference 是 292–306 MB，约 5.76× 差距） |
| 推理表现 | ssim_mean = **0.660** ❌（两次完整 25k iter 均相同） |
| **根因** | NMM Local 模式：每块骨骼生成独立形态键，骨骼数多 → 形态键数量爆炸 → 模型容量远超数据集信息量 → **严重过拟合训练姿态，泛化性极差** |

**关键发现**：模型大小与 Epic Refference 的差距（5.76×）直接暗示架构配置错误，而非数据问题。

---

### 2026-03-07/08 Phase V2 — 根因闭合：Local vs Global 模式对比

通过对 Refference 292-306 MB 参考资产进行尺寸级反推：

> 下表中的 Refference 模式判断属于工作性结论：它解释了为什么 `Global 128` 能把模型容量和指标拉回到接近参考资产的范围，但它本身不是“直接从 Refference 原始工程读取出唯一配置”的证明。

$$207\text{ MB} \approx 128 \times 200,000 \text{ verts} \times 3 \times 4 \text{ B} = 307 \text{ MB}$$

| 维度 | Epic Refference（ssim=0.9142）| 我方 Local 模式（ssim=0.660）|
|------|-------------------------------|-------------------------------|
| **NMM 模式** | **更接近 Global**（基于尺寸/效果反推） | Local（UE 默认）|
| 形态目标数量 | **更接近 128 个全局 morphs** | ~80 bones × 若干 = 480+ 局部基 |
| 模型大小 | **306 MB** | **1680 MB**（5.76× 过大） |
| 训练收敛损失 | ~0.01 | V-3 在 5401 iter 时仍 ≈ 1.44 |
| 过拟合风险 | 低（全局基底共享约束） | 高（每骨骼独立，无共享约束） |

**正确配置**（`pipeline.full_exec.yaml` 中 `deformer_assets.flesh.model_overrides`）：
```yaml
mode: global
global_num_morph_targets: 128
global_num_hidden_layers: 2
global_num_neurons_per_layer: 128
num_iterations: 25000
```

---

### 2026-03-08 Phase V — 闭环达成 ✅

| 参数 | 值 |
|------|-----|
| 模式 | `global` |
| `global_num_morph_targets` | 128 |
| `num_iterations` | 25000 |
| 训练数据 | `upperBodyFlesh_5kGreedyROM` |
| 最终 loss | ~0.011 |
| 训练时长 | ~16 min（956 秒） |
| 模型大小 | **207.1 MB**（vs Refference 306 MB，在合理范围内） |

---

## 四、最终质量指标（1560 帧）

| 指标 | 实测值 | 阈值 | 状态 |
|------|--------|------|------|
| `ssim_mean` | **0.8999** | ≥ 0.83 | ✅ PASS |
| `ssim_p05` | **0.8122** | ≥ 0.70 | ✅ PASS |
| `psnr_mean` | **29.15 dB** | ≥ 22.0 dB | ✅ PASS |
| `psnr_min` | **21.81 dB** | ≥ 14.0 dB | ✅ PASS |
| `edge_iou_mean` | **0.9200** | ≥ 0.82 | ✅ PASS |
| `ms_ssim_mean` | **0.8659** | ≥ 0.80 | ✅ PASS |
| `ms_ssim_p05` | **0.7179** | ≥ 0.65 | ✅ PASS |
| `de2000_mean` | **2.156** | ≤ 8.0 | ✅ PASS |
| `de2000_p95` | **4.755** | ≤ 15.0 | ✅ PASS |

> 与 Epic Refference（ssim=0.9142）对比：我方 0.8999，差距仅 1.4 个百分点。

---

## 五、关键技术决策说明

### 4.1 GPU TDR 修复（d3dadapter=1）

UE 默认选择 D3D12 adapter 0（主显卡，超频至 2535 MHz，在 NNE DirectML 推理负载下不稳定）。  
**修复**：在 UE 命令行参数中增加 `-d3dadapter=1`，强制使用第二张 GPU（无输出信号，稳定）。

```yaml
# pipeline.full_exec.yaml
ue:
  ground_truth:
    capture:
      extra_ue_cmd_args: ["-d3dadapter=1"]
```

### 4.2 UE 崩溃帧累积恢复机制

gt_source_capture 阶段 UE 在 Phase V 期间崩溃 3 次（exit code -1），分别在约 18%、43%、62.7% 处。  
管线的 **resume 逻辑**（`ue_capture_mainseq.py`）将每次崩溃前已完成的帧累积保存，  
重启后从上次中断点继续，最终全部 1560 帧成功捕获。

### 4.3 配置键名称（关键陷阱）

NMM Global 模式的配置键名为 `global_num_morph_targets`，  
**不是** `num_global_morphs`、`num_morph_targets` 或其他变体。  
Local 模式对应键名为 `local_num_morph_targets_per_bone`。

---

## 六、失败模式汇总（本项目经验）

| 失败类型 | 现象 | 根因 | 修复 |
|----------|------|------|------|
| smoke GC 单位错误 | near-black 帧，ssim≈0.59 | Houdini 导出 ABC 时单位换算错误，顶点偏移 90+ cm | 使用 PDG 原始 5kGreedyROM GC |
| OOD 姿态 | ssim≈0.637，全窗口均匀下降 | 训练集 pose 覆盖不足（hero64 5065 帧） | 使用 5kGreedyROM 5k 帧 |
| Local 模式过参数化 | ssim≈0.660，模型 1680 MB | NMM 默认 Local 模式每骨骼生成形态键，过拟合 | 切换 Global 128 模式 |
| GPU TDR 崩溃 | UE 启动后快速 exit=-1 | 主 GPU 超频，DirectML 负载下不稳定 | `-d3dadapter=1` 选择副卡 |
| 训练后资产未更新 | UE exit=-1 但代码认为成功 | UE 训练偶发崩溃，train_report 未写入 | 检查 train_report.json 存在再继续 |

---

## 七、后续建议

1. **增加 `global_num_morph_targets: 256`**：V3 实验（未完成）预期可进一步提高 ssim；建议作为下一个实验分支。
2. **推理延迟 profile**：207 MB 模型尚未在目标硬件上做实时延迟测试（`STAT_MLDeformerInference`）。
3. **Houdini ABC 导出 QC 自动化**：在 `houdini_export_abc.py` 中增加 outputs.bin 顶点偏移分布检查（p50_max > 30 cm 自动 fail），防止 smoke GC 类问题重现。
4. **文档打包交付**：本里程碑 + 新手导航指南（`docs/guide/`）可作为项目交付文档的基础。

---

## 八、关联文档

| 文档 | 路径 |
|------|------|
| Phase V 闭环 checkpoint | `UE57/docs/memory/checkpoint-20260308-phase-V-closure.md` |
| Phase V2 根因分析 | `UE57/docs/memory/checkpoint-20260308-phase-V2-global-mode-root-cause.md` |
| Phase T 调查记录 | `UE57/docs/memory/checkpoint-20260305-phase-T-v4b-nmm-baseline-confirmed.md` |
| Phase TI NMM 调查 | `UE57/docs/memory/phase-TI-nmm-training-investigation.md` |
| Phase U 视觉确认 | `UE57/docs/memory/checkpoint-20260305-phase-U-visual-confirm.md` |
| Smoke 验证汇总 | `memories/repo/smoke_validation_summary.md` |

---

## 九、归档资产说明（GitHub Release）

**Release tag**：`phase-v-closure`  
**存档时间**：2026-03-08  
**包含文件（共 6 个 uasset）**：

| 文件 | 大小 | 日期 | 说明 |
|------|------|------|------|
| `MLD_NMMl_flesh_upperBody.uasset` | 207.1 MB | 2026-03-08 | Phase V 训练产出，ssim=0.8999，Global 128 形态目标 |
| `MLD_NN_lowerCostume.uasset` | 245.7 MB | 2026-03-02 | NNM 下装变形器 |
| `MLD_NN_upperCostume.uasset` | 541.2 MB | 2026-03-02 | NNM 上装变形器 |
| `DG_DQ_Morph_RecomputeNormals.uasset` | 0.1 MB | 2026-02-02 | DQ Groom 辅助资产 |
| `DG_LBS_Morph_RecomputeNormals.uasset` | 0.1 MB | 2026-02-02 | LBS Groom 辅助资产 |
| `Emil_MeshDeformerCollection.uasset` | <1 MB | 2026-02-02 | Deformer 连接集合 |

> ⚠️ **路径陷阱**：以上文件来源于 `D:\UE\Unreal Projects\UE57\MLDeformerSample\Content\Characters\Emil\Deformers\`（pipeline 的实际训练路径），  
> **而非** `D:\UE\Unreal Projects\MLDeformerSample\UE57\Content\Characters\Emil\Deformers\`（git worktree 对比副本，存储的是 2月2日旧版本，292 MB flesh）。  
> 两个路径名相似，请务必通过文件大小和时间戳验证来源。
