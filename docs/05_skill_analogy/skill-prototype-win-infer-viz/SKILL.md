---
name: prototype-win-infer-viz
description: Run Windows-side inference from training artifacts and visualize method-level quality/latency metrics.
---

# Prototype Windows Infer & Viz Skill

## trigger
- 训练完成后需要验证推理链路。
- 需要输出可对比的误差/时延图。
- 需要给阶段评审提供可读结果。

## prerequisites
- `D:/MLDPrototypeData/artifacts/train` 下已存在训练报告。
- Windows 可运行 PowerShell 与 Jupyter。
- Python 已安装 `pandas`、`matplotlib`。

## steps
1. 执行推理：`./prototype/scripts/infer_win.ps1 -DataRoot D:/MLDPrototypeData`。
2. 打开可视化：`jupyter notebook ./prototype/scripts/visualize_win.ipynb`。
3. 在 Notebook 中读取 `infer_reports_index.json` 并绘图。
4. 导出图表用于阶段评审（可选）。

## outputs
- `D:/MLDPrototypeData/artifacts/infer/<method>/infer_report.json`
- `D:/MLDPrototypeData/artifacts/infer/<method>/pred_vs_gt.csv`
- `D:/MLDPrototypeData/artifacts/infer/infer_reports_index.json`

## failure_modes
- 缺少训练报告导致推理脚本中断。
- Notebook 路径错误导致读取失败。
- 图形依赖缺失导致绘图失败。

## verification
- 三个方法都有 `infer_report.json`。
- `infer_reports_index.json` 可被 Notebook 读取。
- 图表中出现 NMM/NNM/Groom 三组结果。
