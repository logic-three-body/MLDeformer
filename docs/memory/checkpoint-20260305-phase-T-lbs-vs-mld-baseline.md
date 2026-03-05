# Checkpoint: Phase T — LBS-ref vs MLD-src Baseline Measurement
**Date:** 2026-03-05  
**Run:** `20260301_162455_smoke`  
**Commit:** `53f3e72` (UE57)

---

## Summary

Phase T measured the pixel-level difference between the LBS (no deformer) reference
and the MLD-active source render. This quantifies how much ML Deformer changes
the character's appearance vs the skinning-only baseline.

---

## Results

| Metric         | Measured | Threshold | Status |
|----------------|----------|-----------|--------|
| ssim_mean      | 0.8832   | ≥ 0.83    | PASS   |
| ssim_p05       | 0.7622   | ≥ 0.70    | PASS   |
| psnr_mean      | 24.78 dB | ≥ 22.0    | PASS   |
| psnr_min       | 16.82 dB | ≥ 14.0    | PASS   |
| edge_iou_mean  | 0.8802   | ≥ 0.82    | PASS   |
| ms_ssim_mean   | 0.8534   | ≥ 0.80    | PASS   |
| ms_ssim_p05    | 0.7063   | ≥ 0.65    | PASS   |
| de2000_mean    | 3.62     | ≤ 8.0     | PASS   |
| de2000_p95     | 6.82     | ≤ 15.0    | PASS   |

**All 9 metrics: PASS**

For comparison — Phase S (LBS-vs-LBS identical render):
- ssim_mean = 0.9994 (deterministic identical renders)

The ~0.12 SSIM drop (0.9994 → 0.8832) represents the MLD deformation magnitude.

---

## Method

Source capture used the **static_source_frames_dir bypass** pointing to the
2/26 MLD-active capture (`20260226_200951_smoke`), because the 2GB NMM model
updated on 2026-03-03 crashes UE game-mode after a 25-second silent hang (exit -1).

- **Reference frames:** Captured 2026-03-04 from UE57 project with
  `-DemoDisableMLDeformer=1` (LBS only), warmup=100, 1560 frames.
- **Source frames:** Captured 2026-02-26 with MLD active (pre-3/3 NMM model,
  `MLD_NMMl_flesh_upperBody.uasset` = 306 MB), warmup=16, 1560 frames.

---

## 2GB NMM Crash — Open Issue

The `MLD_NMMl_flesh_upperBody.uasset` was re-saved on 2026-03-03 17:18:51 and
is now 2,081,083,042 bytes (~2 GB, 6.8× larger than the 306 MB Refference copy).
This model crashes UE in game-mode (`-game` flag) after a ~25-second silent hang,
exit code -1, no crash dump.

**Root cause chain:**
1. `NNERuntimeBasicCpu` is used by ALL MLD models (NeuralMorphModel, NearestNeighborModel)
2. On `BeginPlay`, `NNERuntimeBasicCpu::CreateModelData()` calls `FMemory::Malloc(2 GB)`
   + `FMemory::Memcpy(2 GB)`, then creates an ORT session from the 2 GB buffer
3. Something during ORT session creation for a 2 GB ONNX model causes exit -1
   (possibly OOM, DX12 resource exhaustion, or uncaught C++ exception)
4. Working run 2/26 used the 306 MB model and loaded successfully in ~21s

**Evidence:**
- 2/26 run: ssim=0.9994 (MLD active), exit=0, duration=110s — worked with old model
- 3/2 16:22: GPU crash in game-mode (new NN costume models)
- 3/3 17:19: UE Editor assert `GetRestoredDimensions` 23s after NMM save
- 3/5 today: exit=-1, 25s silence after AlembicLibrary warning, 0/1560 frames

**Workaround options:**
- Temporary: copy 306 MB Refference NMM to UE57 project for testing
- Permanent: re-train NMM to produce smaller model, or fix memory allocation issue
  in the training/export pipeline

---

## Config Changes (committed `53f3e72`)

```yaml
# pipeline.full_exec.yaml
capture:
  disable_ml_deformer_for_source: false
  static_source_frames_dir: "...runs/20260226_200951_smoke/.../source/frames"
compare:
  thresholds:
    ssim_mean_min: 0.83   # was 0.40 (permissive placeholder)
    psnr_mean_min: 22.0   # was 10.0
    de2000_mean_max: 8.0  # was 30.0
    # ... (all tightened to ~5-10% below measured values)
```

```python
# build_report.py _pipeline_thresholds()
# Was: permissive Phase T placeholders (ssim=0.40, psnr=10.0, de2000=30.0)
# Now: Phase T measured baseline (ssim=0.83, psnr=22.0, de2000=8.0)
```
