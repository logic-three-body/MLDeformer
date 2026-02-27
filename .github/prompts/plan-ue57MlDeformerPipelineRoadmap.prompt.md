# Plan: UE5.7 MLDeformer Pipeline Modification Roadmap (v2 — engine source included)

## TL;DR

Pipeline run `20260226_200951_smoke` passes with relaxed thresholds. The cross-engine quality gap (SSIM=0.845, ΔE=3.13) is real and measurable. This plan hardens the UE57 compat layer, closes remaining API gaps, enables UE5.7 native training, and tightens calibrated thresholds post-training.

## Background

**Current state** (`20260226_200951_smoke`):

| Stage | Status |
|---|---|
| baseline_sync / train / infer | ✅ success (skip_train=true, using UE5.5 pre-trained weights) |
| gt_compare | ✅ success (relaxed thresholds) |
| train_determinism | ⚠️ missing (training skipped) |

**Quality metrics vs two baselines:**

| Metric | Actual | UE5.7 config threshold | UE5.5 strict threshold |
|---|---|---|---|
| ssim_mean | 0.8453 | ≥ 0.80 ✅ | ≥ 0.995 ❌ |
| psnr_mean | 26.47 dB | ≥ 22.0 ✅ | ≥ 35.0 ❌ |
| ms_ssim_mean | 0.7987 | ≥ 0.78 ✅ (+0.019 margin) | ≥ 0.995 ❌ |
| de2000_mean | 3.13 | ≤ 15.0 ✅ | ≤ 1.0 ❌ |

**Frames 400–599 are the degradation hotspot** (ssim_mean=0.760, psnr=21.5dB) — highest dynamic deformation segment.

## Engine API Changes: UE5.5 → UE5.7

| Class/Symbol | UE5.5 | UE5.7 Change | Handled? |
|---|---|---|---|
| `GetMemUsageInBytes()` | main entry | split into `GetMainMemUsageInBytes()` + `GetGPUMemUsageInBytes()` | ✅ multi-name fallback |
| `BoneMaskInfos` / `BoneGroupMaskInfos` | `TMap<FName, FNeuralMorphMaskInfo>` | renamed to `BoneMaskInfoMap`, type changed to `FMLDeformerMaskInfo` | ❌ no rename shim |
| `FNeuralMorphMaskInfo` | NeuralMorphTypes.h | moved to `MLDeformerMasking.h` as `FMLDeformerMaskInfo`, new `MaskMode` (Generated/VertexAttribute) + `VertexAttributeName` | ❌ new fields not handled |
| `EMLDeformerSkinningMode` | not present | **new enum** Linear/DualQuaternion on `UNeuralMorphModel` | ❌ no config path |
| `UNearestNeighborModelSection` | `FClothPartData` struct (deprecated 5.4) | **refactored to UObject**, new `WeightMapCreationMethod`, `AttributeName`, `BoneNames` | ❌ property names not audited |
| `GetNumMorphTargets()` (no args) | main API | deprecated 5.4, new API requires `int32 LOD` param | ❌ LOD param not added |
| `SampleGroundTruthPositions(float)` | main API | deprecated, replaced by `SampleGroundTruthPositionsAtFrame(int32 FrameIndex)` | ⚠️ only hit if skip_train=false |
| `FMLDeformerTrainingDataProcessorAnim` | not present | **new struct** wrapping training animation config | ❌ training currently skipped |
| `mldeformer/` Python package | not present | engine-bundled `morph_helpers`, `training_helpers`, `tensorboard_helpers` | ❌ not documented/integrated |
| `VertexDeltaModel` plugin | not present | **new plugin** | ⬜ out of scope (project doesn't use it) |

---

## Phase 1 — 渲染差距诊断 (Diagnose the rendering gap)

**Goal**: Understand WHY frames 400–599 degrade to SSIM=0.76 / PSNR=21.5dB.

1. **视觉侦察**: Extract worst-frame heatmaps from `gt_compare_report.json` `heatmaps[]` and review visually. Determine if gap is: (a) pure renderer/PP difference, (b) mesh deformation difference, or (c) skinning mode change.
2. **SkinningMode 检查**: Read the deformer asset editor properties in the UE5.7 project to confirm `SkinningMode`. If UE5.7 defaults to `DualQuaternion` for new assets, that alone would drive the deformation gap. (If positive → Phase 2 step 6 becomes P0.)
3. **捕获参数对齐**: Compare `ue_capture_mainseq.py` MovieRenderQueue settings (resolution, AA, post-process volume) between UE5.5 and UE5.7 runs.
4. **帧分布映射**: Check what animations/poses live in frames 400–599 via `profiling_summary.csv`. Confirm whether these are high-deformation dynamic frames.

*No code changes in Phase 1.*

---

## Phase 2 — API Compat Hardening

**Goal**: Defensively handle all UE5.7 API renames that could cause silent failures.

**File to edit**: `UE57/pipeline/hou2ue/scripts/ue_setup_assets.py`

### 2.1 BoneMaskInfos rename shim

In `_apply_model_overrides()`, before `set_editor_property(key, value)`, apply rename map:
```python
_57_RENAME = {
    "bone_mask_infos": "bone_mask_info_map",
    "bone_group_mask_infos": "bone_group_mask_info_map",
}
key = _57_RENAME.get(key, key)
```
Also handle new `FMLDeformerMaskInfo` struct fields (`mask_mode`, `vertex_attribute_name`) in struct constructor, with fallback for old-style dicts.

### 2.2 SkinningMode config support

Add `"skinning_mode": "linear"|"dual_quaternion"` handling inside `_apply_model_overrides()`:
```python
if key == "skinning_mode":
    mode_map = {
        "linear": unreal.EMLDeformerSkinningMode.LINEAR,
        "dual_quaternion": unreal.EMLDeformerSkinningMode.DUAL_QUATERNION,
    }
    model.set_editor_property("skinning_mode", mode_map[value.lower()])
    continue
```

### 2.3 NNM Section property name audit

Read `UNearestNeighborModelSection` in UE5.7 header → confirm property names used in the NNM section override loop. Specifically check: `num_pca_coeffs`, `num_neighbors`, `weight_map_creation_method`, `bone_names`, `attribute_name`. Patch mismatches.

### 2.4 GetNumMorphTargets LOD param

Any call to `model.get_num_morph_targets()` (no args) should become `model.get_num_morph_targets(0)` (LOD=0).

---

## Phase 3 — Enable UE5.7 Native Training

*Depends on Phase 2.*

### 3.1 Config change

In `pipeline.full_exec.yaml`: set `ue.training.skip_train: false` and configure `training_data_source`. Optionally add `skinning_mode` field if Phase 2.2 reveals default differs.

### 3.2 TrainingDataProcessorAnim fallback in ue_train.py

Add version detection:
```python
# Try 5.5 API first; fall back to 5.7 FMLDeformerTrainingDataProcessorAnim wrapper
try:
    model.set_editor_property("training_input_anims", anims_array)
except Exception:
    # 5.7 path: construct FMLDeformerTrainingDataProcessorAnim wrappers
    ...
```

### 3.3 Engine-bundled Python package documentation

Document that `mldeformer/morph_helpers.py`, `training_helpers.py`, `tensorboard_helpers.py` now live at:
`UE_5.7/Engine/Plugins/Animation/MLDeformer/MLDeformerFramework/Content/Python/mldeformer/`

Note division of responsibility vs project-side scripts. Identify any duplicated logic as tech debt.

### 3.4 Train determinism verification

After first successful UE5.7 training:
- Run training twice with same `HOU2UE_TRAIN_SEED`
- Hash the `.nmn` artifacts
- Write result to `train_determinism_report.json`

---

## Phase 4 — Calibrated Threshold Update

*Depends on Phase 3.*

1. Re-run `compare_groundtruth.py` with the freshly trained UE5.7 model.
2. Expected improvement: SSIM ~0.89+, ΔE ~1.5–2.0 (same-gen training data → less cross-version deformation divergence).
3. Update `pipeline.full_exec.yaml` thresholds to `actual * 0.97` (3% margin) for all metrics.
4. Set `debug_mode: false` — confirm `pipeline_report_latest.json` still `status=success`.

---

## Phase 5 — Checklist & Docs Update

1. Tick off `README_UE57_Migration_Checklist_CN.md` items B1–B6 and E1–E8.
2. Update `docs/02_code_map/` with UE5.7 diffs:
   - New plugin `VertexDeltaModel`
   - `EMLDeformerSkinningMode` enum
   - `FMLDeformerMaskInfo` new fields (`MaskMode`, `VertexAttributeName`)
   - `UNearestNeighborModelSection` UObject refactor (vs old `FClothPartData` struct)
   - `SampleGroundTruthPositionsAtFrame` signature change
3. Add a doc section for the engine-bundled `mldeformer/` Python package.

---

## Relevant Files

| File | Phase |
|---|---|
| `UE57/pipeline/hou2ue/scripts/ue_setup_assets.py` | 2.1, 2.2, 2.3, 2.4 |
| `UE57/pipeline/hou2ue/scripts/ue_train.py` | 3.2, 3.4 |
| `UE57/pipeline/hou2ue/config/pipeline.full_exec.yaml` | 3.1, 4 |
| `D:\Program Files\Epic Games\UE_5.7\Engine\Plugins\Animation\MLDeformer\NearestNeighborModel\Source\NearestNeighborModel\Public\NearestNeighborModel.h` | 2.3 (reference) |
| `D:\Program Files\Epic Games\UE_5.7\Engine\Plugins\Animation\MLDeformer\MLDeformerFramework\Source\MLDeformerFramework\Public\MLDeformerMorphModel.h` | 2.4 (reference) |
| `UE57/docs/07_ue57_compat/README_UE57_Migration_Checklist_CN.md` | 5.1 |
| `docs/02_code_map/` | 5.2, 5.3 |

## Verification Criteria

1. **Phase 2**: `ue_setup.log` shows no `set_editor_property` type errors or "deprecated property" warnings.
2. **Phase 3**: `.nmn` artifact generated; training log has no Python exceptions.
3. **Phase 3.4**: Two trains with same seed produce byte-identical `.nmn` → `train_determinism_status: success`.
4. **Phase 4**: `pipeline_report_latest.json` `status=success` with `debug_mode=false`, `errors=[]`.

## Decisions / Scope

- **Out of scope**: `VertexDeltaModel`, `ChaosClothGenerator`, `ChaosFleshGenerator` plugins (project doesn't use them)
- **In scope**: NMM + NNM compat only (Ada / Emil / Cylinder characters use these two models)
- **Assumption**: Frames 400–599 quality drop is primarily renderer-side (not model error); Phase 3 re-training may shrink but not eliminate the gap
- **Phase 1 gates Phase 2 priority**: If `SkinningMode` is confirmed `DualQuaternion` default → step 2.2 becomes P0 and is implemented immediately before other Phase 2 steps
- **Phase 3 risk**: If `FMLDeformerTrainingDataProcessorAnim` is not fully Python-reflected, a C++ `BlueprintCallable` wrapper may need to be added to the project's `MLDeformerSampleEditorTools` module
