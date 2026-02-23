#!/usr/bin/env python3
"""UE import stage: bring FBX/ABC assets into project with idempotent update behavior."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

import unreal

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from ue_common import (
    apply_template,
    finalize_report,
    get_context,
    make_report,
    require_nested,
    write_stage_report,
)


def _set_prop_safe(obj: Any, name: str, value: Any) -> None:
    try:
        obj.set_editor_property(name, value)
    except Exception:
        pass


def _split_asset(asset_path: str) -> tuple[str, str]:
    folder, name = asset_path.rsplit("/", 1)
    return folder, name


def _ensure_folder(folder: str) -> None:
    if not unreal.EditorAssetLibrary.does_directory_exist(folder):
        unreal.EditorAssetLibrary.make_directory(folder)


def _asset_exists(asset_path: str) -> bool:
    return unreal.EditorAssetLibrary.does_asset_exist(asset_path)


def _build_fbx_options(import_kind: str, skeleton: Optional[unreal.Skeleton]) -> unreal.FbxImportUI:
    options = unreal.FbxImportUI()
    _set_prop_safe(options, "automated_import_should_detect_type", False)
    _set_prop_safe(options, "import_materials", False)
    _set_prop_safe(options, "import_textures", False)

    if import_kind == "skeletal_mesh":
        _set_prop_safe(options, "import_mesh", True)
        _set_prop_safe(options, "import_as_skeletal", True)
        _set_prop_safe(options, "import_animations", False)
        _set_prop_safe(options, "mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    elif import_kind == "animation":
        _set_prop_safe(options, "import_mesh", False)
        _set_prop_safe(options, "import_as_skeletal", False)
        _set_prop_safe(options, "import_animations", True)
        _set_prop_safe(options, "mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
        if skeleton is not None:
            _set_prop_safe(options, "skeleton", skeleton)
    else:
        raise RuntimeError(f"Unsupported FBX import kind: {import_kind}")

    return options


def _build_abc_options() -> Optional[unreal.AbcImportSettings]:
    try:
        options = unreal.AbcImportSettings()
        _set_prop_safe(options, "import_type", unreal.AlembicImportType.GEOMETRY_CACHE)
        # Keep source track/object names so MLDeformer can match against skeletal mesh geometry parts.
        try:
            gc_settings = options.get_editor_property("geometry_cache_settings")
            if gc_settings is not None:
                _set_prop_safe(gc_settings, "flatten_tracks", False)
                _set_prop_safe(gc_settings, "store_imported_vertex_numbers", True)
                _set_prop_safe(gc_settings, "b_store_imported_vertex_numbers", True)
                _set_prop_safe(options, "geometry_cache_settings", gc_settings)
        except Exception:
            pass
        return options
    except Exception:
        return None


def _run_import_task(
    source_file: Path,
    destination_asset: str,
    options: Any,
) -> Dict[str, Any]:
    folder, name = _split_asset(destination_asset)
    _ensure_folder(folder)

    existed = _asset_exists(destination_asset)

    task = unreal.AssetImportTask()
    task.filename = str(source_file)
    task.destination_path = folder
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.replace_existing_settings = True
    task.save = True
    if options is not None:
        task.options = options

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    imported = [str(v) for v in task.get_editor_property("imported_object_paths")]
    status = "update" if existed else "create"

    result = {
        "source": str(source_file),
        "destination": destination_asset,
        "status": status,
        "imported_object_paths": imported,
        "success": len(imported) > 0 or _asset_exists(destination_asset),
    }

    if isinstance(options, unreal.AbcImportSettings):
        abc_settings: Dict[str, Any] = {}
        try:
            gc_settings = options.get_editor_property("geometry_cache_settings")
            if gc_settings is not None:
                for key in (
                    "flatten_tracks",
                    "store_imported_vertex_numbers",
                    "b_store_imported_vertex_numbers",
                    "apply_constant_topology_optimizations",
                ):
                    try:
                        abc_settings[key] = gc_settings.get_editor_property(key)
                    except Exception:
                        pass
        except Exception:
            pass
        if abc_settings:
            result["abc_import_settings"] = abc_settings

    if not result["success"]:
        result["status"] = "failed"
        result["error"] = "No imported object paths and destination asset missing"

    return result


def _load_body_skeleton(body_mesh_asset: str) -> Optional[unreal.Skeleton]:
    skm = unreal.load_asset(body_mesh_asset)
    if skm is None:
        return None
    try:
        skeleton = skm.get_editor_property("skeleton")
        if isinstance(skeleton, unreal.Skeleton):
            return skeleton
    except Exception:
        return None
    return None


def main() -> int:
    ctx = get_context()
    cfg = ctx["config"]
    run_dir: Path = ctx["run_dir"]
    profile: str = ctx["profile"]

    report = make_report(
        "ue_import",
        profile,
        {
            "config": str(ctx["config_path"]),
            "profile": profile,
            "run_dir": str(run_dir),
        },
    )

    try:
        art_root = Path(require_nested(cfg, ("paths", "art_source_root")))
        if not art_root.exists():
            raise RuntimeError(f"ArtSource path does not exist: {art_root}")

        import_cfg = require_nested(cfg, ("ue", "imports"))
        skm_jobs = list(require_nested(import_cfg, ("skeletal_meshes",)))
        anim_jobs = list(require_nested(import_cfg, ("animations",)))

        results: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []

        # 1) Skeletal meshes.
        for job in skm_jobs:
            src = art_root / str(require_nested(job, ("source_rel",)))
            dst = str(require_nested(job, ("destination",)))
            if not src.exists():
                errors.append({"message": f"Missing source file: {src}", "destination": dst})
                continue
            options = _build_fbx_options("skeletal_mesh", skeleton=None)
            result = _run_import_task(src, dst, options)
            results.append(result)
            if not result["success"]:
                errors.append({"message": result.get("error", "Import failed"), "destination": dst})

        # 2) Load skeleton from body mesh for animation import.
        body_mesh_asset = "/Game/Characters/Emil/Models/Body/skm_Emil"
        body_skeleton = _load_body_skeleton(body_mesh_asset)

        # 3) Animations.
        for job in anim_jobs:
            src = art_root / str(require_nested(job, ("source_rel",)))
            dst = str(require_nested(job, ("destination",)))
            if not src.exists():
                errors.append({"message": f"Missing source file: {src}", "destination": dst})
                continue
            options = _build_fbx_options("animation", skeleton=body_skeleton)
            result = _run_import_task(src, dst, options)
            results.append(result)
            if not result["success"]:
                errors.append({"message": result.get("error", "Import failed"), "destination": dst})

        # 4) Dynamic flesh geometry cache from convert stage output.
        dynamic_cfg = require_nested(cfg, ("ue", "dynamic_assets"))
        gc_dst_template = str(require_nested(dynamic_cfg, ("flesh_geom_cache_destination_template",)))
        gc_dst = apply_template(gc_dst_template, profile)

        gc_src = run_dir / "workspace" / "staging" / profile / "houdini_exports" / f"GC_upperBodyFlesh_{profile}.abc"
        if not gc_src.exists():
            errors.append({
                "message": "Missing Houdini export Alembic for UE import",
                "source": str(gc_src),
                "destination": gc_dst,
            })
        else:
            result = _run_import_task(gc_src, gc_dst, _build_abc_options())
            results.append(result)
            if not result["success"]:
                errors.append({"message": result.get("error", "GeomCache import failed"), "destination": gc_dst})

        # 5) Optional NNM geometry caches (upper/lower costume), exported during convert stage.
        for key in (
            "nnm_upper_geom_cache_destination_template",
            "nnm_lower_geom_cache_destination_template",
        ):
            template = str(dynamic_cfg.get(key, "") or "").strip()
            if not template:
                continue

            dst_asset = apply_template(template, profile)
            asset_name = dst_asset.rsplit("/", 1)[-1]
            src_abc = run_dir / "workspace" / "staging" / profile / "houdini_exports" / f"{asset_name}.abc"
            if not src_abc.exists():
                errors.append(
                    {
                        "message": "Missing NNM Alembic export for UE import",
                        "source": str(src_abc),
                        "destination": dst_asset,
                    }
                )
                continue

            result = _run_import_task(src_abc, dst_asset, _build_abc_options())
            results.append(result)
            if not result["success"]:
                errors.append({"message": result.get("error", "GeomCache import failed"), "destination": dst_asset})

        status = "success" if not errors else "failed"
        finalize_report(
            report,
            status=status,
            outputs={
                "asset_results": results,
                "imported_count": len([r for r in results if r.get("success")]),
                "failed_count": len(errors),
                "body_skeleton_loaded": body_skeleton is not None,
            },
            errors=errors,
        )

        write_stage_report(run_dir, "ue_import", report)
        return 0 if status == "success" else 1

    except Exception as exc:
        finalize_report(
            report,
            status="failed",
            outputs={},
            errors=[{"message": str(exc), "traceback": traceback.format_exc()}],
        )
        write_stage_report(run_dir, "ue_import", report)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
