#!/usr/bin/env python3
"""Create/configure ML Deformer assets for NMM + NNM via C++ bridge."""

from __future__ import annotations

import csv
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Tuple

import unreal

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from ue_common import (
    apply_template,
    asset_exists,
    finalize_report,
    get_context,
    load_asset_checked,
    make_report,
    require_nested,
    save_asset,
    split_asset_path,
    write_stage_report,
)


def _setup_request_class():
    for name in ("MldSetupRequest", "FMldSetupRequest"):
        cls = getattr(unreal, name, None)
        if cls is not None:
            return cls
    raise RuntimeError("Cannot find MldSetupRequest struct in Unreal Python API")


def _set_field_safe(obj: Any, key: str, value: Any) -> bool:
    try:
        obj.set_editor_property(key, value)
        return True
    except Exception:
        return False


def _get_field_safe(obj: Any, key: str, default: Any = None) -> Any:
    try:
        return obj.get_editor_property(key)
    except Exception:
        return default


def _ensure_asset(asset_path: str) -> Tuple[Any, str]:
    if asset_exists(asset_path):
        return load_asset_checked(asset_path), "update"

    folder, name = split_asset_path(asset_path)
    if not unreal.EditorAssetLibrary.does_directory_exist(folder):
        unreal.EditorAssetLibrary.make_directory(folder)

    factory = unreal.MLDeformerFactory()
    created = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name=name,
        package_path=folder,
        asset_class=unreal.MLDeformerAsset,
        factory=factory,
    )
    if created is None:
        raise RuntimeError(f"Failed to create ML Deformer asset: {asset_path}")
    return created, "create"


def _infer_frame_range_from_pose_map(run_dir: Path, profile: str) -> Tuple[int, int] | None:
    pose_map = run_dir / "workspace" / "staging" / profile / "houdini_exports" / "pose_frame_map.csv"
    if not pose_map.exists():
        return None

    sample_count = 0
    with pose_map.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        for row in reader:
            if row:
                sample_count += 1

    if sample_count <= 0:
        return None
    return (0, sample_count - 1)


def _resolve_training_inputs(
    items: List[Dict[str, Any]],
    profile: str,
    inferred_range: Tuple[int, int] | None = None,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for raw in items:
        item = dict(raw)
        if "geometry_cache_template" in item and not item.get("geometry_cache"):
            item["geometry_cache"] = apply_template(str(item.get("geometry_cache_template") or ""), profile)

        explicit_range = any(k in item for k in ("use_custom_range", "start_frame", "end_frame"))
        if not explicit_range and inferred_range is not None:
            item["use_custom_range"] = True
            item["start_frame"] = int(inferred_range[0])
            item["end_frame"] = int(inferred_range[1])

        out.append(item)
    return out


def _resolve_nnm_sections(items: List[Dict[str, Any]], profile: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for raw in items:
        item = dict(raw)
        if "neighbor_meshes_template" in item and not item.get("neighbor_meshes"):
            item["neighbor_meshes"] = apply_template(str(item.get("neighbor_meshes_template") or ""), profile)
        out.append(item)
    return out


def _build_setup_request(
    cfg: Dict[str, Any],
    profile: str,
    run_dir: Path,
    key: str,
):
    req = _setup_request_class()()

    asset_path = str(require_nested(cfg, ("asset_path",)))
    model_type = str(require_nested(cfg, ("model_type",)))
    skeletal_mesh = str(require_nested(cfg, ("skeletal_mesh",)))
    deformer_graph = str(cfg.get("deformer_graph", "") or "")
    test_anim_sequence = str(cfg.get("test_anim_sequence", "") or "")
    model_overrides = dict(cfg.get("model_overrides", {}))

    inferred_range = _infer_frame_range_from_pose_map(run_dir, profile) if key == "flesh" else None
    resolved_inputs = _resolve_training_inputs(list(cfg.get("training_input_anims", [])), profile, inferred_range)
    resolved_sections = _resolve_nnm_sections(list(cfg.get("nnm_section_overrides", [])), profile)

    _set_field_safe(req, "asset_path", asset_path)
    _set_field_safe(req, "model_type", model_type)
    _set_field_safe(req, "skeletal_mesh", skeletal_mesh)
    _set_field_safe(req, "deformer_graph", deformer_graph)
    _set_field_safe(req, "test_anim_sequence", test_anim_sequence)
    _set_field_safe(req, "training_input_anims_json", json.dumps(resolved_inputs, ensure_ascii=True))
    _set_field_safe(req, "model_overrides_json", json.dumps(model_overrides, ensure_ascii=True))
    _set_field_safe(req, "nnm_sections_json", json.dumps(resolved_sections, ensure_ascii=True))
    _set_field_safe(req, "force_switch", True)

    return req, resolved_inputs


def _configure_single_asset(name: str, cfg: Dict[str, Any], profile: str, run_dir: Path) -> Dict[str, Any]:
    asset_path = str(require_nested(cfg, ("asset_path",)))
    model_type = str(require_nested(cfg, ("model_type",)))
    _, lifecycle = _ensure_asset(asset_path)

    lib = getattr(unreal, "MLDTrainAutomationLibrary", None)
    if lib is None:
        raise RuntimeError("MLDTrainAutomationLibrary class missing; cannot configure assets")

    fn = getattr(lib, "setup_deformer_asset", None)
    if fn is None:
        raise RuntimeError("setup_deformer_asset missing in MLDTrainAutomationLibrary")

    req, resolved_inputs = _build_setup_request(cfg, profile, run_dir, name)
    result = fn(req)

    success = bool(_get_field_safe(result, "success", False))
    message = str(_get_field_safe(result, "message", ""))
    warnings = list(_get_field_safe(result, "warnings", []) or [])

    save_asset(asset_path)
    status = "success" if success else "failed"
    return {
        "name": name,
        "asset_path": asset_path,
        "model_type": model_type,
        "lifecycle": lifecycle,
        "status": status,
        "message": message,
        "warnings": [str(w) for w in warnings],
        "resolved_training_input_anims": resolved_inputs,
    }


def main() -> int:
    ctx = get_context()
    cfg = ctx["config"]
    run_dir = ctx["run_dir"]
    profile = ctx["profile"]

    report = make_report(
        "ue_setup",
        profile,
        {
            "config": str(ctx["config_path"]),
            "run_dir": str(run_dir),
            "profile": profile,
        },
    )

    try:
        assets_cfg = require_nested(cfg, ("ue", "deformer_assets"))
        ordered_keys = list(require_nested(cfg, ("ue", "training_order")))

        results: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        for key in ordered_keys:
            item_cfg = assets_cfg.get(key)
            if not isinstance(item_cfg, dict):
                errors.append({"message": f"Missing deformer_assets entry for '{key}'"})
                continue

            try:
                res = _configure_single_asset(key, item_cfg, profile, run_dir)
                results.append(res)
                if res["status"] != "success":
                    errors.append({"message": f"Asset setup failed: {key}", "detail": res.get("message", "")})
            except Exception as exc:
                errors.append(
                    {
                        "message": f"Exception while configuring asset '{key}': {exc}",
                        "traceback": traceback.format_exc(),
                    }
                )

        status = "success" if not errors else "failed"
        finalize_report(
            report,
            status=status,
            outputs={
                "asset_results": results,
                "success_count": len([r for r in results if r.get("status") == "success"]),
                "failure_count": len(errors),
            },
            errors=errors,
        )
        write_stage_report(run_dir, "ue_setup", report)
        return 0 if status == "success" else 1

    except Exception as exc:
        finalize_report(
            report,
            status="failed",
            outputs={},
            errors=[{"message": str(exc), "traceback": traceback.format_exc()}],
        )
        write_stage_report(run_dir, "ue_setup", report)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
