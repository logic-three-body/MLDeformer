# Checkpoint: Phase T v3 — NMM Regression Fixed (2026-03-05)

## Run
`20260305_141106_smoke` in UE57 sub-repo

## Summary
NMM model regression confirmed and fixed. Phase T v3 passes all metrics.

## Metrics (1560 frames, MLD active, pre-training 306 MB NMM model)

| Metric      | Value  | Threshold | Pass |
|-------------|--------|-----------|------|
| ssim_mean   | 0.9142 | ≥ 0.83    | ✅   |
| psnr_mean   | 30.63  | ≥ 22.0 dB | ✅   |
| de2000_mean | 1.584  | ≤ 8.0     | ✅   |

All 9 pipeline thresholds PASS.

## Root Cause (March 3 Training Regression)
Training wrote harmful vertex offsets into NMM morph targets.
2 GB uasset produced near-black frames in shots 5-6 via backface culling.

## Fix
Restored pre-training 306 MB model from Refference (Feb 1 2026).
Pipeline uproject: `D:\UE\Unreal Projects\UE57\MLDeformerSample\Content\...`

## Phase History

| Phase     | ssim_mean | Result  |
|-----------|-----------|---------|
| S (LBS)   | 0.9994    | PASS    |
| T bypass  | 0.8832    | PASS    |
| T v2 (↓)  | 0.5904    | FAIL    |
| T v3 (✅) | 0.9142    | PASS    |

## UE57 Repo Commit
`6ed4371` — Phase T v3: NMM regression FIXED -- ssim=0.9142 PASS
