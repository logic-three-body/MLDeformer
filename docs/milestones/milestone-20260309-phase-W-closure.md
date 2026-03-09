# 里程碑：Phase W 闭环 — W-3B NNM smoke PASS

**日期：** 2026-03-09  
**状态：** ✅ 闭环达成  
**最终指标：** `ssim_mean = 0.9960`，`ssim_p05 = 0.9929`，`psnr_mean = 52.28 dB`，`edge_iou_mean = 0.9942`

---

## 一、执行摘要

Phase W 原本的目标只是把 Phase V / W-2C 一直卡住的 `ssim≈0.900x` 推过 `0.91`。最终结果不是小幅越线，而是在 W-3B NNM 分支上把 smoke 全链路指标直接抬到接近逐帧重合的水平：

- `ue_setup`：success
- `train`：success（前 2 次启动级失败后，第 3 次自动重试成功）
- `gt_reference_capture`：success
- `gt_source_capture`：success
- `gt_compare`：success
- `report`：success

隔离 run dir：`UE57/pipeline/hou2ue/workspace/runs/20260309_164800_smoke_w3b_nnm`

---

## 二、为什么 W-3A 和 W-3B 差别这么大

最核心的原因是：**这两个方案不是“同一方向的不同强度”，而是在解决完全不同的问题。**

### 1. W-2C 暴露的问题不是全局容量不够，而是局部姿态簇误差

W-2C 已经证明：

- `global_num_morph_targets` 从 128 扩到 256、512，没有带来实质性收益；
- `global_num_neurons_per_layer` 从 128 扩到 256，也几乎没有改变 `ssim`；
- `num_iterations` 从 25k 拉到 50k，loss 虽下降 27%，但 `ssim` 仍停在 `0.9004`。

这说明瓶颈不是“再给 Global NMM 更多统一容量”，而是**某些局部、连续、姿态相关帧簇的误差模式**。自动分析已经把主瓶颈钉在 `0588–0597` 和 `0600–0699`。

### 2. W-3A 受限 Local 本质上是在削弱表达能力

W-3A 使用的是：

```yaml
mode: local
local_num_morph_targets_per_bone: 1
num_iterations: 25000
```

这个试探的目的，是验证“只给每骨骼极小局部容量”是否还能覆盖主瓶颈。但结果表明它把表达能力压得过低：

- `ssim_mean = 0.5550`
- `ssim_p05 = 0.4389`
- `edge_iou_mean = 0.4619`

同时 `outputs.bin` QC 仍通过，说明这不是训练数据坏掉，而是**模型路线本身不成立**。换句话说，W-3A 不是“差一点”，而是把问题从“局部误差”放大成了“整体表达崩塌”。

### 3. W-3B NNM 走的是“检索相似姿态 + 局部细节融合”路线

W-3B 沿用同一套已验证的 flesh 训练输入：

- `upperBodyFlesh_5kGreedyROM`
- `GC_upperBodyFlesh_5kGreedyROM`

但把 flesh 资产切到 `model_type: NNM`，并引入：

- `neighbor_poses`
- `neighbor_meshes_template`
- `num_pca_coeffs: 64`
- `num_basis_per_section: 64`

这条路线没有去硬砍形变容量，而是让模型在基础网络之外，使用**相似姿态邻域**去补足 W-2C 最弱的那类局部形变。对于 `0588–0597 / 0600–0699` 这种“不是全局都差，而是某一簇姿态明显偏”的场景，这正好是对症方案。

### 4. 结果说明：此前的主误差是“检索/局部补偿问题”，不是“全局网络大小问题”

W-3B 最终结果：

| 指标 | W-2C | W-3A Local | W-3B NNM |
|------|------|------------|----------|
| `ssim_mean` | `0.9004` | `0.5550` | **`0.9960`** |
| `ssim_p05` | `0.8104` | `0.4389` | **`0.9929`** |
| `psnr_mean` | `29.57 dB` | `14.37 dB` | **`52.28 dB`** |
| `edge_iou_mean` | `0.9208` | `0.4619` | **`0.9942`** |

关键窗口也同步恢复：

- `0500–0599`: `ssim_mean = 0.9946`
- `0600–0699`: `ssim_mean = 0.9964`

这说明真正奏效的不是“继续给 NMM 加统一容量”，而是**让模型能够在相似姿态邻域内重建局部细节**。

---

## 三、W-3B 实验配置

```yaml
config: UE57/pipeline/hou2ue/config/pipeline.phase_w_w3b_nnm.yaml
run_dir: UE57/pipeline/hou2ue/workspace/runs/20260309_164800_smoke_w3b_nnm
asset_path: /Game/Characters/Emil/Deformers/MLD_NMMl_flesh_upperBody
model_type: NNM
neighbor_poses: /Game/Characters/Emil/Animation/MLD_train/upperBodyFlesh_5kGreedyROM
neighbor_meshes_template: /Game/Characters/Emil/GeomCache/MLD_Train/GC_upperBodyFlesh_5kGreedyROM
num_pca_coeffs: 64
num_basis_per_section: 64
num_iterations: 5000
```

---

## 四、最终 smoke 结果

| 指标 | 值 |
|------|----|
| `ssim_mean` | `0.9960` |
| `ssim_p05` | `0.9929` |
| `psnr_mean` | `52.28 dB` |
| `psnr_min` | `44.69 dB` |
| `edge_iou_mean` | `0.9942` |
| `ms_ssim_mean` | `0.9979` |
| `de2000_mean` | `0.2339` |
| `body_roi_ssim_mean` | `0.9943` |

严格阈值也全部满足：`ssim_mean>=0.995`、`ssim_p05>=0.985`、`psnr_mean>=35`、`edge_iou>=0.97`。

---

## 五、执行细节与注意事项

1. `ue_setup` 必须先在隔离 run dir 内执行，否则很容易把“配置已改”误判成“资产已生效”。
2. `train` 阶段前 2 次尝试都在 checkpoint 前退出，但 `run_all.ps1` 自动重试后第 3 次成功完成，不应仅凭前两次启动失败就提前回滚方案。
3. `report.outputs_bin_qc` 在 NNM 分支上仍引用 `Intermediate/NeuralMorphModel/outputs.bin`，所以它只能做旁证；NNM 是否通过，应以隔离 run dir 的 `gt_reference_capture + gt_source_capture + gt_compare` 结果为准。

---

## 六、产物与文档

| 项目 | 路径 |
|------|------|
| W-3B config | `UE57/pipeline/hou2ue/config/pipeline.phase_w_w3b_nnm.yaml` |
| run dir | `UE57/pipeline/hou2ue/workspace/runs/20260309_164800_smoke_w3b_nnm` |
| review sheets | `UE57/pipeline/hou2ue/workspace/runs/20260309_164800_smoke_w3b_nnm/reports/review_sheets/` |
| kickoff log | `docs/milestones/milestone-20260308-phase-W-kickoff.md` |
| plan | `docs/plan/phase_W_plan.md` |

---

## 七、结论

Phase W 的最终结论不是“Global 256 终于调通”，而是：

> **对 Emil flesh 这条 smoke 闭环，真正有效的不是继续扩大 Global NMM 容量，而是切换到基于相似姿态邻域融合的 NNM 路线。**

这也解释了为什么 W-3A 和 W-3B 的结果不是同量级差异，而是几乎一个失败分支和一个闭环分支的差异。