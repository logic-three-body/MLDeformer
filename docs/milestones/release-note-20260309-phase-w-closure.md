# Release Note — 2026-03-09 Phase W Closure

## Summary

Phase W is now closed on the W-3B NNM path.

- Final smoke result: `ssim_mean=0.9960`
- Key bottleneck windows `0588–0597 / 0600–0699` recovered to `0.99x`
- W-3A constrained Local was retained as a negative control and is now documented as a failed branch

## What Changed

- Added a formal closure milestone for Phase W
- Updated the kickoff and plan documents so they no longer stop at W-2C
- Added beginner-guide and theory-layer writeups explaining why constrained Local failed while NNM succeeded
- Added UE5.7 code-map and compatibility writebacks so the result is documented as a model-path decision, not an API-migration accident

## Key Lesson

The decisive lesson from this milestone is that the bottleneck was not global NMM capacity.
It was a local, pose-cluster-specific reconstruction problem.

- W-3A constrained Local reduced per-bone capacity too aggressively and collapsed overall expressivity
- W-3B NNM preserved a stable base prediction, then used nearest-neighbor detail fusion to repair the exact kind of clustered local error that W-2C exposed

## Main References

- `docs/milestones/milestone-20260309-phase-W-closure.md`
- `docs/milestones/milestone-20260308-phase-W-kickoff.md`
- `docs/plan/phase_W_plan.md`
- `UE57/docs/02_code_map/README_UE57_CodeMap_Diff_CN.md`
- `UE57/docs/07_ue57_compat/README_UE57_Breaking_Changes_CN.md`
- `UE57/docs/07_ue57_compat/README_UE57_Migration_Checklist_CN.md`