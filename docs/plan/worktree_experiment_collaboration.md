# Worktree 多分支实验协作方案

> **创建日期**: 2026-03-07  
> **阶段**: Phase V — NMM 架构调参  
> **背景**: Phase U 两次训练均 ssim≈0.660（失败），根因为 NMM 模型无 morph 数量约束（1680 MB vs Refference 292 MB）。

---

## 1. 目的

为了并行准备多种修复方案（而不必等每次 3 小时训练结果再决定下一步），使用 `git worktree` 在多个独立目录中维护不同的实验配置，通过 `run_experiment.ps1` 依次执行并对比结果。

---

## 2. 目录结构

```
D:\UE\
├── Unreal Projects\MLDeformerSample\   ← 主 repo (branch: master)
│   ├── pipeline\hou2ue\config\
│   │   └── pipeline.full_exec.yaml     ← V-1 配置 (local_num_morph=1)
│   ├── pipeline\hou2ue\run_experiment.ps1
│   └── UE57\pipeline\hou2ue\           ← 运行时（gitignored）
│       ├── config\pipeline.full_exec.yaml  ← 实验运行前由 run_experiment.ps1 同步
│       └── run_experiment.ps1          ← 运行入口（从 pipeline\ 复制）
├── WT_V2\                              ← worktree (branch: experiment/V-2)
│   └── pipeline\hou2ue\config\pipeline.full_exec.yaml
├── WT_V3\                              ← worktree (branch: experiment/V-3)
│   └── pipeline\hou2ue\config\pipeline.full_exec.yaml
└── WT_V4\                              ← worktree (branch: experiment/V-4)
    └── pipeline\hou2ue\config\pipeline.full_exec.yaml
```

---

## 3. 实验矩阵

| 实验 | 分支 | Worktree | `local_num_morph_targets_per_bone` | 其他变化 | 预期模型大小 | 状态 |
|------|------|----------|-------------------------------------|----------|------------|------|
| **V-1** | `master` | `MLDeformerSample\` | **1** | — | ~280 MB | 🔄 训练中 |
| **V-2** | `experiment/V-2` | `D:\UE\WT_V2` | **2** | — | ~560 MB | ⏳ 待机 |
| **V-3** | `experiment/V-3` | `D:\UE\WT_V3` | 1 | `neurons=12, hidden=2` | ~280 MB | ⏳ 待机 |
| **V-4** | `experiment/V-4` | `D:\UE\WT_V4` | — | `skip_train=true` + `disable_ml_deformer=true` | — (LBS sanity) | ⏳ 随时可跑 |

**验收标准**: `ssim_mean ≥ 0.83`（最低通过）/ `ssim_mean ≥ 0.91`（理想对齐 Refference）

---

## 4. 运行方式

### 4a. 主入口：`run_experiment.ps1`

```powershell
# 运行 V-1（当前 master 配置，local_num_morph=1）
& "D:\UE\Unreal Projects\MLDeformerSample\UE57\pipeline\hou2ue\run_experiment.ps1" -Exp V-1

# 运行 V-2（local_num_morph=2）
& "D:\UE\Unreal Projects\MLDeformerSample\UE57\pipeline\hou2ue\run_experiment.ps1" -Exp V-2

# 运行 V-3（更深网络）
& "D:\UE\Unreal Projects\MLDeformerSample\UE57\pipeline\hou2ue\run_experiment.ps1" -Exp V-3

# 运行 V-4（LBS sanity，无需训练，快速）
& "D:\UE\Unreal Projects\MLDeformerSample\UE57\pipeline\hou2ue\run_experiment.ps1" -Exp V-4
```

### 4b. `run_experiment.ps1` 执行流程

```
1. 从 <worktree>/pipeline/hou2ue/config/pipeline.full_exec.yaml
   → 复制到 D:\UE\...\UE57\pipeline\hou2ue\config\pipeline.full_exec.yaml

2. run_all.ps1 -Stage train     (V-4 跳过)
3. run_all.ps1 -Stage gt_source_capture
4. run_all.ps1 -Stage gt_compare
5. 清理 stale report_report.json
6. run_all.ps1 -Stage report
7. 打印 ssim/psnr 结果摘要
```

日志保存在 `UE57\pipeline\hou2ue\workspace\exp_V-X_TIMESTAMP.log`

---

## 5. 迭代决策树

```
V-4 (LBS sanity) ───→ ssim ≈ 1.0? ─→ YES: 管线 OK，问题在模型
                                    ─→ NO:  管线本身有问题，先修管线

V-1 (local=1, ~280MB)
  ─→ ssim ≥ 0.83? ─→ YES: ✅ 闭环成功！合并到 master → 提交测试
  ─→ ssim ∈ [0.70,0.83)? ─→ 运行 V-3 (更深网络) 再试
  ─→ ssim < 0.70? ─→ 运行 V-2 (local=2, more capacity) + V-3

V-3 (深网络, ~280MB)
  ─→ ssim ≥ 0.83? ─→ ✅ 闭环成功！合并到 master
  ─→ FAIL? ─→ 运行 V-2

V-2 (local=2, ~560MB)
  ─→ ssim ≥ 0.83? ─→ ✅ 闭环成功！合并到 master
  ─→ FAIL? ─→ 需要更深入分析（可能是 GC 质量、anim sequence 问题）
```

---

## 6. 优先执行顺序

1. **V-4 先跑**（约 30 min，无训练）→ 验证管线基础健康
2. **V-1 等待结果**（正在训练，约 2.5h）→ 最主要假设
3. 根据 V-1 结果决定是否运行 V-3 / V-2

---

## 7. 合并策略

当某个实验 PASS，在主 repo 执行：

```powershell
cd "D:\UE\Unreal Projects\MLDeformerSample"

# 例如 V-2 通过，合并其配置回 master
git merge experiment/V-2 --no-ff -m "merge: V-2 config (local_num_morph=2) — ssim=0.XX PASS"

# 清理已用 worktree
git worktree remove "D:\UE\WT_V2"
git worktree remove "D:\UE\WT_V3"
git worktree remove "D:\UE\WT_V4"
git branch -d experiment/V-2 experiment/V-3 experiment/V-4   # 删除未用分支

git push origin master
```

---

## 8. Worktree 管理命令速查

```powershell
# 列出所有 worktree
git -C "D:\UE\Unreal Projects\MLDeformerSample" worktree list

# 修剪已删除的 worktree 条目
git -C "D:\UE\Unreal Projects\MLDeformerSample" worktree prune

# 在 worktree 中查看 diff
git -C "D:\UE\WT_V2" diff HEAD

# 添加新实验（如需 V-5）
git -C "D:\UE\Unreal Projects\MLDeformerSample" worktree add "D:\UE\WT_V5" -b experiment/V-5
# 修改 D:\UE\WT_V5\pipeline\hou2ue\config\pipeline.full_exec.yaml
# git -C "D:\UE\WT_V5" add/commit
# run_experiment.ps1 -Exp custom -WorktreePath "D:\UE\WT_V5"
```

---

## 9. 关键文件路径速查

| 文件 | 路径 | 说明 |
|------|------|------|
| 主运行脚本 | `UE57/pipeline/hou2ue/run_experiment.ps1` | 调度器 |
| 旧运行脚本 | `UE57/pipeline/hou2ue/run_all.ps1` | 底层执行 |
| 监控脚本 | `UE57/pipeline/hou2ue/workspace/chain_monitor.ps1` | 自动监控链（旧） |
| V-1 config | `pipeline/hou2ue/config/pipeline.full_exec.yaml` (master) | local=1 |
| V-2 config | `D:\UE\WT_V2\pipeline\hou2ue\config\pipeline.full_exec.yaml` | local=2 |
| V-3 config | `D:\UE\WT_V3\pipeline\hou2ue\config\pipeline.full_exec.yaml` | local=1+deeper |
| V-4 config | `D:\UE\WT_V4\pipeline\hou2ue\config\pipeline.full_exec.yaml` | LBS sanity |
| UE Saved Log | `D:\UE\Unreal Projects\UE57\MLDeformerSample\Saved\Logs\MLDeformerSample.log` | 训练进度 |
| 比较报告 | `UE57/pipeline/hou2ue/workspace/latest/smoke/reports/gt_compare_report.json` | ssim/psnr |
