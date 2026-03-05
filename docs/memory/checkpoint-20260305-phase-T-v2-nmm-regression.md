# Checkpoint: Phase T v2 — Real MLD Capture, NMM Regression Detected
**Date:** 2026-03-05  
**Run:** `20260305_130217_smoke`  
**Commit:** `609a33d` (UE57)

---

## Summary

Phase T v2 performed a live MLD source capture using the new 2GB NMM model
(`MLD_NMMl_flesh_upperBody.uasset`, 2026-03-03). All 1560 frames were captured
with `warmup_frames=16` and `disable_ml_deformer_for_source=false`.

Metrics show a **severe quality regression** compared to the bypass measurement
(Phase T, 2/26 model, ssim=0.8832 PASS). The new model fails all thresholds.

---

## Results

| Metric        | Measured  | Threshold | Status |
|---------------|-----------|-----------|--------|
| ssim_mean     | 0.5904    | ≥ 0.83    | **FAIL** |
| psnr_mean     | 14.51 dB  | ≥ 22.0    | **FAIL** |
| de2000_mean   | 17.09     | ≤ 8.0     | **FAIL** |

**All 3 primary metrics: FAIL**

For comparison — Phase T bypass (2/26 model):
- ssim_mean = 0.8832 (PASS)

---

## Root Cause

The 2GB NMM model (`MLD_NMMl_flesh_upperBody.uasset`, 2026-03-03) produces
geometrically invalid vertex offsets in shots 5–6 (frames 1231–1428), causing
backface culling → near-black source frames.

| Frame  | src_mean | ref_mean | ratio |
|--------|----------|----------|-------|
| .0050  | 66.6     | 58.5     | 1.14  | (normal)
| .0387  | 49.2     | 94.8     | 0.52  | (dark start)
| .1000  | 30.3     | 89.7     | 0.34  | (very dark)
| .1415  | 16.5     | 77.1     | 0.21  | (nearly BLACK)
| .1430  | 105.8    | 100.3    | 1.05  | (shot 7 recovers — NORMAL)

Shot 7 (frames 1429–1559) recovers spontaneously. The regression is
shot-dependent and affects only shots 5–6 of the 7-shot sequence.

---

## Capture Details

- **Source:** 1560 frames, MLD active, warmup=16, 165.6s (exit=0, success)
- **Reference:** 1560 frames, static bypass from `20260301_162455_smoke`
  (LBS-only frames captured 2026-03-01)
- **Config changes from Phase T bypass:**
  - `warmup_frames`: 100 → 16
  - `static_source_frames_dir`: cleared (live capture)
  - `static_reference_frames_dir`: set to LBS baseline run
  - `disable_ml_deformer_for_source`: false

---

## Bug Fixed: build_report.py Windows Junction

`_copy_latest()` in `build_report.py` called `shutil.rmtree(latest_dir)` on a
Windows directory junction, raising `OSError: Cannot call rmtree on a symbolic link`.

**Fix:** Catch `OSError` and fall back to `os.rmdir(str(latest_dir))` which
removes only the junction leaf without touching the target directory.

---

## Action Required

The new 2GB NMM model needs review/retraining:
- Old model (2/26, 306 MB): ssim=0.8832 PASS
- New model (3/3, 2 GB): ssim=0.5904 FAIL

Thresholds correctly flag this regression. **Do NOT lower thresholds.**
The model likely needs: weight inspection, retraining, or rollback to pre-3/3.
