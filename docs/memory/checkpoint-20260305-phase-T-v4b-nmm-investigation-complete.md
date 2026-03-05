# Checkpoint: Phase T v4b — NMM Training Investigation Complete (2026-03-05)

## Summary

Completed full NMM training root cause investigation. Key findings:

- **T v4 (hero64 training test)**: ssim=0.637 ❌ — training GC quality was fine (p50=4.0 cm) but pose coverage insufficient for Main_Sequence generalization
- **T v4b (Refference NMM restored)**: ssim=0.9142 ✅ — stable baseline confirmed; identical to T v3

Current validated stable baseline: **ssim=0.9142** (Refference NMM 306 MB, Epic-trained).

---

## NMM Training Investigation Results

### Root Cause of T v2 Failure (Confirmed)
`GC_upperBodyFlesh_smoke` (1.65 GB, 2026-03-01 from Houdini pipeline) had extreme vertex offsets:
- p50_max = 90.7 cm (should be < 30 cm for upper body tissue deformation)
- max = 148.7 cm (1.5 m — physically impossible)
- 675/1001 frames (67%) with max offset > 80 cm

**Origin**: Houdini smoke profile GC export has wrong unit scaling or unnormalized tissue sim data.

### hero64 GC Training (T v4 Test)
Used `GC_upperBodyFlesh_hero64` (117 MB, Feb 2, PDG validated) as training data:
- Training quality: p50_max=4.0 cm, 0/5065 frames > 80 cm ✅
- Inference result: ssim=0.637 ❌ (all 16 windows 0.49-0.80)
- **Failure reason**: hero64 animation covers only hero64 poses; Main_Sequence has different/broader pose space; NMM extrapolates poorly outside training distribution

### Epic Refference NMM (306 MB) — Still Best Available
The Epic-trained NMM generalizes to Main_Sequence presumably because it was trained on comprehensive pose data (full sequence, properly exported GC). This remains the only working NMM for the demo.

---

## Phase T Execution History (Complete)

| Phase | Run Dir | NMM | ssim_mean | Result |
|-------|---------|-----|-----------|--------|
| S (LBS baseline) | `20260226_200951_smoke` | disabled | 0.9994 | ✅ PASS |
| T bypass | `20260226_200951_smoke` | Ref 306 MB | 0.8832 | ✅ PASS |
| T v2 (train regression) | `20260305_130217_smoke` | 2 GB trained | 0.5904 | ❌ FAIL |
| T v3 (rollback) | `20260305_141106_smoke` | Ref 306 MB | 0.9142 | ✅ PASS |
| T v4 (hero64 train test) | `20260305_141106_smoke` | 357 MB hero64 | 0.637 | ❌ FAIL |
| **T v4b (confirmed)** | `20260305_141106_smoke` | Ref 306 MB | **0.9142** | ✅ PASS |

---

## Asset State

| Asset | Size | Status |
|-------|------|--------|
| `MLD_NMMl_flesh_upperBody.uasset` | **306 MB** | ✅ Refference (working) |
| `.uasset.2gb_backup_20260303` | 1985 MB | 🗄️ bad March 3 training |
| `.uasset.hero64_backup_20260305` | 374 MB | 🗄️ hero64 training (ineffective) |
| `MLD_NN_lowerCostume.uasset` | 258 MB | ✅ March 2 trained (valid) |
| `MLD_NN_upperCostume.uasset` | 568 MB | ✅ March 2 trained (valid) |

---

## Open Items (Future Work)

1. **Fix Houdini smoke GC export** — correct unit scaling in `.hip` workflow
2. **Retrain NMM** with fixed smoke GC + `upperBody_7000` (full pose coverage)
3. **Investigate `num_iterations:2000`** config not overriding UE5.7 NMM default (25,000 used)

UE57 repo commit: `6b49bde` (4 files, 232 insertions)
