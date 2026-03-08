# Plan: Phase W - challenge ssim >= 0.91 (align Epic Refference 0.9142)

## TL;DR
Phase V 稳定在 ssim=0.8999。Phase W 目标 ssim ≥ 0.91，通过增加 NMM Global morph targets（128 → 256）实现。  
W-1 训练已完成（2026-03-08），frame 1054 上臂肌肉形变问题已记录，根据 ssim 结果决定是否启动 W-2。

## 基线
- Phase V：Global 128 morphs，207 MB，ssim=0.8999，loss=0.011，25k iter，~16 min
- Epic Refference：306 MB，ssim=0.9142
- 差距：1.43% absolute SSIM

## W-1 主实验：Global 256 morphs（已完成）

**假设**：
- 256 个全局形态基底可提升上臂等细节区域的变形捕获精度
- 全局 morphs 共享约束，过拟合风险低于 Local 模式

**配置（pipeline.full_exec.yaml）**：
```yaml
mode: global
global_num_morph_targets: 256
global_num_hidden_layers: 2
global_num_neurons_per_layer: 128
num_iterations: 25000
```

**W-1 结果**：
| 项目 | 值 |
|------|-----|
| 训练状态 | ✅ 完成（status: success） |
| ended_at | 2026-03-08T10:39:14Z |
| 模型大小 | 207.1 MB（uasset，UE 内部压缩） |
| 最终 loss | ~0.011 |
| gt_source_capture | ✅ 完成 |
| gt_compare | ✅ 完成 |
| ssim_mean | **0.9005** |
| 达标 | ❌ 未达标（目标 ≥ 0.91）|

**视觉质量问题（frame 1054）**：
> 上臂肌肉在特定姿态下与参考存在可感知的形变偏差。
- 位置：Main Sequence frame 1054 / 1560（约 67.6%）
- 问题：Global morphs 分布全身，上臂专属容量有限；网络宽度（128 neurons）预测精度受限

**决策门**：
- ssim ≥ 0.91 → Phase W 闭环，frame 1054 记录为已知轻微缺陷
- 0.83 ≤ ssim < 0.91 → 启动 W-2 架构调参（见下方）
- ssim < 0.83 → 回退 Phase V 128 morphs

---

## W-2A 备用调参（256 morphs + 256 neurons）——已完成

**配置**：`global_num_neurons_per_layer: 256`（128→256）

**W-2A 结果**：
| 项目 | 值 |
|------|-----|
| ended_at | 2026-03-08T13:35:42Z |
| ssim_mean | **0.9006**（vs W-1 0.9005，提升 +0.0001）|
| ssim_p05 | 0.8120 |
| ms_ssim | 0.8670 |
| psnr | 29.26 dB |
| 达标 | ❌ 未达标 |

> **关键结论**：neurons 翻倍提升几乎为零（δ = +0.0001）。morphs 和 neurons 均非瓶颈。
> 三次实验累计：Phase V(0.8999) → W-1(+0.0006) → W-2A(+0.0001) = **总提升 +0.0007**。
> 新假设：训练数据覆盖度（pose distribution）或 morph 数量需大幅增加才能送出改善。

---

## W-2B 备用调参（512 morphs ——**已完成**）

**动机**：全局 512 morphs 让上臂区域获得更多全知形态化，测试 morph 数量大幅增加对质量上限的影响。

**配置**：
```yaml
global_num_morph_targets: 512  # 256 → 512
global_num_neurons_per_layer: 256  # 保持 W-2A
```

**W-2B 结果**：
| 项目 | 值 |
|------|-----|
| ended_at | 2026-03-08T15:03:00Z |
| ssim_mean | **0.9000**（vs W-2A 0.9006，**下降 -0.0006**）|
| ssim_p05 | 0.8121 |
| ms_ssim | 0.8661 |
| psnr | 29.18 dB |
| 达标 | ❌ 未达标 |

> ⚠️ **退步原因**：512 morphs 在 25k iters 内收敛不足（欠拟合）。
> **四轮汇总**：Phase V(0.8999) → W-1(0.9005) → W-2A(0.9006) → W-2B(0.9000)
> **结论**：ssim 上限约 0.90，架构容量配置无关，根因需重新调查。

---

## W-2C 전최종（256 morphs + 256 neurons + 50k iters——**완료**）

> **중요 배경**: ue_setup을 먼저 실행한 첫 번째 실험. W-1/W-2A/W-2B는 모두 Phase V 구조(128m/128n)로 실제 훈련됨.
> VRAM 증거: W-1/2A/2B = 1.14 GB (Phase V), W-2C = **1.79 GB** (256 neurons 실제 적용 확인).

**설정**:
```yaml
global_num_morph_targets: 256
global_num_neurons_per_layer: 256
num_iterations: 50000
```

**W-2C 결과**:
| 항목 | 값 |
|------|-----|
| ue_setup | success, ended_at: 2026-03-08T16:00:00Z (1.79 GB 확인) |
| ended_at | 2026-03-08T19:23:26Z |
| 최종 loss | ~0.00808 (vs Phase V ~0.011, **-27%**) |
| ssim_mean | **0.9004**（vs W-2A 0.9006, -0.0002） |
| ssim_p05 | 0.8104 |
| ms_ssim | 0.8657 |
| psnr | **29.57 dB**（vs W-2A 29.26, **+0.31 dB**）|
| de2000 | **2.138**（vs W-2A 2.141, 소폭 개선）|
| edge_iou | 0.9208 |
| 달성 | ❌ 미달（목표 ≥ 0.91）|

> **W-2C 핵심 결론**:
> - Loss -27%에도 ssim은 거의 변화 없음 → **loss와 ssim 해리(decouple)**.
> - Phase W 5회 실험(Phase V → W-2C) ssim 범위: 0.900–0.9006 (진폭 0.0007).
> - NMM Global 모드: morphs/neurons 용량, 반복 횟수 모두 ssim 병목이 아님.
> - **W-3 전략 전환 필요 (아래 참조)**.

---

## W-3 전략 전환 방향（검토 중）

Phase W 결과 요약:

| 실험 | 실제 구조 | ssim | 비고 |
|------|---------|------|------|
| Phase V | 128m/128n/25k | 0.8999 | 기준 |
| W-1 | 128m/128n/25k (ue_setup 미적용) | 0.9005 | 가짜 256m |
| W-2A | 128m/128n/25k (ue_setup 미적용) | 0.9006 | 가짜 256n |
| W-2B | 128m/128n/25k (ue_setup 미적용) | 0.9000 | 가짜 512m |
| W-2C | **256m/256n/50k** (ue_setup 정상) | **0.9004** | 첫 진짜 실험 |
| 목표 | Epic Ref | **0.9142** | 차이 -0.0138 |

**가능한 W-3 접근 방식**:
1. **Local 모드 전환**: 신체 구역별 전용 NMM → 상완 전용 용량 확보
2. **NearestNeighborModel(NNM)**: 유사 포즈 기반 보간 → 데이터 커버리지 문제 완화 가능
3. **훈련 데이터 분석**: 5kGreedyROM pose 분포, frame 1054 유사 포즈 커버리지 확인
4. **Ground truth 품질 검토**: gt_source 렌더링 자체에 ceiling이 있는지 확인

---

## W-3 QC Gate（W-1 后独立验证）

目标：防止 smoke GC 数据质量问题重现。

实现状态：
- 已在 `build_report.py` report 阶段增加 QC gate
- 配置于 `report.outputs_bin_qc`，阈值 30.0 cm
- pipeline 失败时作为报告失败项输出

---

## 执行命令

```powershell
# 训练
& "D:/UE/Unreal Projects/MLDeformerSample/UE57/pipeline/hou2ue/run_all.ps1" `
  -Stage train `
  -Config "D:/UE/Unreal Projects/MLDeformerSample/UE57/pipeline/hou2ue/config/pipeline.full_exec.yaml" `
  -Profile smoke

# 验证链（含 QC gate）
& "D:/UE/Unreal Projects/MLDeformerSample/UE57/pipeline/hou2ue/run_all.ps1" `
  -Stage gt_source_capture,gt_compare,report `
  -Config "D:/UE/Unreal Projects/MLDeformerSample/UE57/pipeline/hou2ue/config/pipeline.full_exec.yaml" `
  -Profile smoke
```

---

## 验证检查项

1. train_report.json status = success
2. gt_compare ssim_mean ≥ 0.91（W-1 目标）
3. report 阶段 outputs.bin QC gate 通过（p50_max ≤ 30 cm）
4. frame 1054 上臂形变差异主观可接受
5. 如达标：commit `feat: Phase W Global 256 morphs ssim>=0.91`

---

## 相关文件

- `UE57/pipeline/hou2ue/config/pipeline.full_exec.yaml`
- `UE57/pipeline/hou2ue/scripts/build_report.py`
- `docs/milestones/milestone-20260308-phase-W-kickoff.md`
- `docs/plan/phase_W_plan.md`
