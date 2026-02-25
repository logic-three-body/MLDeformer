# Checkpoint 20260226 - Full Validation + Skip_train Shortcut + Color GT

## 1. 概述
- **触发事件**：完成 P1-P5 全部优先级任务。
- **核心成果**：
  1. Full profile 验证通过 (46 pose frames)
  2. 3x 稳定性复跑全部通过 (3/3 smoke)
  3. skip_train 快捷通道实现并验证（节省 ~30% 时间）
  4. 彩色 GT 对比指标实现
  5. Lower costume demo 路线分析完成（确认已隐式覆盖）

## 2. P1: Full Profile 验证

### Run: `20260225_215842_full`
| 指标 | 实测值 | strict 阈值 | 结果 |
|---|---|---|---|
| ssim_mean | 0.9955 | ≥ 0.995 | ✅ |
| ssim_p05 | 0.9953 | ≥ 0.985 | ✅ |
| psnr_mean | 53.36 | ≥ 35.0 | ✅ |
| psnr_min | 52.21 | ≥ 30.0 | ✅ |
| edge_iou | 0.9874 | ≥ 0.97 | ✅ |

- Profile: `full` (46 pose frames, maxprocs=10)
- 耗时: ~30 min
- 全 11 阶段 success，0 errors

## 3. P2: 3x 稳定性复跑

| Run | SSIM | SSIM p05 | PSNR | PSNR min | EdgeIoU | 结果 |
|---|---|---|---|---|---|---|
| `20260225_223734_smoke` | 0.9969 | 0.9954 | 55.86 | 52.45 | 0.9891 | ✅ |
| `20260225_230707_smoke` | 0.9958 | 0.9953 | 54.14 | 52.26 | 0.9877 | ✅ |
| `20260225_234041_smoke` | 0.9975 | 0.9954 | 57.25 | 52.45 | 0.9906 | ✅ |

- **3/3 全部通过** strict 阈值
- SSIM 范围: [0.9958, 0.9975]，PSNR 范围: [54.14, 57.25]
- 说明 skip_train 模式下管线输出高度稳定

## 4. P3: skip_train 快捷通道

### 改动
1. **`run_all.ps1`**: 当 `skip_train=true` 且 `-Stage full` 时，自动跳过 `preflight`, `houdini`, `convert`, `ue_import` 四个阶段（GeomCache 在 skip_train 模式下不被消费）
2. **`build_report.py`**: 对 skip_train 快捷模式下缺失的阶段报告标记为 `skipped_skip_train` 而非 `missing`（不触发 failure）

### 验证: Run `20260226_001602_smoke`
- 阶段状态：
  - baseline_sync: success
  - preflight: **skipped_skip_train**
  - houdini: **skipped_skip_train**
  - convert: **skipped_skip_train**
  - ue_import: **skipped_skip_train**
  - ue_setup ~ report: success
- SSIM=0.9986, status=success, 0 errors
- **耗时: 23 min vs 32.8 min (节省 30%)**

## 5. P4: 彩色 GT 对比指标

### 改动
- `compare_groundtruth.py`: 新增 `_load_rgb()`, `_ssim_color()`, `_psnr_color()` 函数
- 每帧追加计算 RGB SSIM (3通道均值) 和 RGB PSNR
- 输出新增指标: `color_ssim_mean`, `color_ssim_p05`, `color_psnr_mean`, `color_psnr_min`
- window_metrics 也包含 `color_ssim_mean`, `color_psnr_mean`
- **不影响现有 gate 判定**（彩色指标为补充监控，不参与 pass/fail 决策）

### 验证结果（Run 20260226_001602_smoke 重跑 gt_compare）
| 指标 | 灰度 | 彩色 |
|---|---|---|
| SSIM mean | 0.9986 | 0.9984 |
| PSNR mean | 59.53 | 59.44 |
| SSIM p05 | — | 0.9946 |
| PSNR min | — | 52.15 |

- 彩色指标略低于灰度（符合预期，RGB 通道更敏感）
- 无色彩回归问题

## 6. P5: Lower Costume Demo 路线

### 分析结论
- 当前 2 条 demo 路线 (`LS_NMM_Local`, `LS_NearestNeighbour`) 渲染的 Emil 角色同时激活了全部 3 个 ML Deformer 模型（NMM flesh + NNM upper + NNM lower）
- lower_costume 已在画面中**隐式呈现**，GT 全帧对比会捕获任何下装退化
- 创建独立下装 LevelSequence 需 UE Editor 手动操作（无法从代码生成 .uasset）
- **结论**：当前覆盖度已足够，标记为已知限制而非阻塞问题

## 7. 文件变更

| 文件 | 变更内容 |
|---|---|
| `pipeline/hou2ue/run_all.ps1` | skip_train 快捷通道（跳过 preflight/houdini/convert/ue_import） |
| `pipeline/hou2ue/scripts/build_report.py` | skip_train 阶段报告容错（`skipped_skip_train` 状态） |
| `pipeline/hou2ue/scripts/compare_groundtruth.py` | 彩色 SSIM/PSNR 指标（`_load_rgb`, `_ssim_color`, `_psnr_color`） |

## 8. Git Tag
- `v0.2.0-strict-pass`: 打在 P1-P5 前的基线状态
- `v0.3.0-validated`: 打在本次提交（包含所有优化和验证）
