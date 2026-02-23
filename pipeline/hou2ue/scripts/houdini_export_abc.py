#!/usr/bin/env python3
"""Convert Houdini caches into a UE geometry-cache Alembic + pose map.

Primary path:
- consume selected sample list from run_manifest (`selected_outputs.tissue_training_files`)
- build a temporary bgeo sequence
- export a single Alembic by running hython + Alembic ROP (`use_sop_path`)
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import traceback
from pathlib import Path
from typing import Any, Dict, List, Tuple

from common import (
    apply_template,
    ConfigError,
    finalize_report,
    load_config,
    load_json,
    make_report,
    require_nested,
    stage_report_path,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export stitched Alembic for UE training")
    parser.add_argument("--config", required=True)
    parser.add_argument("--profile", required=True, choices=["smoke", "full"])
    parser.add_argument("--run-dir", required=True)
    return parser.parse_args()


def _extract_index(path: Path) -> int:
    # For sim names like Mio_tissue_sim.10.0001.bgeo.sc, use the last numeric token (0001).
    matches = re.findall(r"\d+", path.name)
    if matches:
        return int(matches[-1])
    return 10**9


def _sorted_by_index(paths: List[Path]) -> List[Path]:
    return sorted(paths, key=lambda p: (_extract_index(p), p.name.lower()))


def _find_hython(cfg: Dict[str, Any]) -> Path:
    configured = str(require_nested(cfg, ("paths", "houdini", "hython_exe")))
    hython = Path(configured)
    if not hython.exists():
        raise RuntimeError(f"hython executable not found: {hython}")
    return hython


def _extract_source_frame(path: Path) -> int:
    # mesh style: Mio_tissue_mesh_580.bgeo.sc
    m_mesh = re.search(r"_mesh_(\d+)", path.name)
    if m_mesh:
        return int(m_mesh.group(1))

    # sim style: Mio_tissue_sim.10.0004.bgeo.sc -> frame=4
    m_sim = re.search(r"\.(\d+)\.(\d+)\.bgeo", path.name)
    if m_sim:
        return int(m_sim.group(2))

    nums = re.findall(r"\d+", path.name)
    if nums:
        return int(nums[-1])
    return -1


def _hardlink_or_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    try:
        os.link(src, dst)
    except Exception:
        shutil.copy2(src, dst)


def _build_sequence_files(source_files: List[Path], seq_dir: Path) -> Tuple[str, int]:
    if not source_files:
        raise RuntimeError("No source files supplied for Alembic export")

    seq_dir.mkdir(parents=True, exist_ok=True)
    for old in seq_dir.glob("*"):
        if old.is_file():
            old.unlink()

    for idx, src in enumerate(source_files, start=1):
        dst = seq_dir / f"frame.{idx:04d}.bgeo.sc"
        _hardlink_or_copy(src, dst)

    # Avoid end-frame overread by duplicating the last frame once.
    final_src = seq_dir / f"frame.{len(source_files):04d}.bgeo.sc"
    final_dup = seq_dir / f"frame.{len(source_files) + 1:04d}.bgeo.sc"
    _hardlink_or_copy(final_src, final_dup)

    pattern = (seq_dir / "frame.$F4.bgeo.sc").as_posix()
    return pattern, len(source_files)


def _run_hython_abc_export(
    hython: Path,
    seq_pattern: str,
    frame_count: int,
    output_abc: Path,
    track_sop_name: str = "body_mesh",
) -> Dict[str, Any]:
    script = "\n".join(
        [
            "import hou",
            f"seq_pattern = {json.dumps(seq_pattern)}",
            f"output_abc = {json.dumps(output_abc.as_posix())}",
            f"frame_count = {int(frame_count)}",
            f"track_sop_name = {json.dumps(track_sop_name)}",
            "hou.hipFile.clear(suppress_save_prompt=True)",
            "obj = hou.node('/obj')",
            "geo = obj.createNode('geo', 'hou2ue_export_geo')",
            "for child in list(geo.children()):",
            "    child.destroy()",
            "file_sop = geo.createNode('file', track_sop_name)",
            "file_sop.parm('file').set(seq_pattern)",
            "file_sop.setDisplayFlag(True)",
            "file_sop.setRenderFlag(True)",
            "outnet = hou.node('/out')",
            "rop = outnet.createNode('alembic', 'hou2ue_export_rop')",
            "rop.parm('use_sop_path').set(1)",
            "rop.parm('sop_path').set(file_sop.path())",
            "rop.parm('filename').set(output_abc)",
            "rop.parm('mkpath').set(1)",
            "rop.render(frame_range=(1, frame_count, 1), verbose=False)",
            "print(output_abc)",
        ]
    )

    result = subprocess.run(
        [str(hython), "-"],
        input=script,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "hython Alembic export failed with non-zero exit code. "
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
    if not output_abc.exists():
        raise RuntimeError(
            "hython Alembic export finished without output file. "
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
    return {
        "stdout_tail": result.stdout[-4000:],
        "stderr_tail": result.stderr[-4000:],
    }


def _run_hython_fbx_to_abc_export(
    hython: Path,
    fbx_file: Path,
    output_abc: Path,
    preferred_geo_obj: str,
    frame_start: int,
    frame_end: int,
    track_sop_name: str = "",
    strip_prim_name_attrs: bool = False,
) -> Dict[str, Any]:
    if frame_end < frame_start:
        frame_end = frame_start

    script = "\n".join(
        [
            "import hou",
            f"fbx_file = {json.dumps(fbx_file.as_posix())}",
            f"output_abc = {json.dumps(output_abc.as_posix())}",
            f"preferred_geo_obj = {json.dumps(preferred_geo_obj)}",
            f"frame_start = {int(frame_start)}",
            f"frame_end = {int(frame_end)}",
            f"track_sop_name = {json.dumps(track_sop_name)}",
            f"strip_prim_name_attrs = {bool(strip_prim_name_attrs)}",
            "hou.hipFile.clear(suppress_save_prompt=True)",
            "root, _ = hou.hipFile.importFBX(fbx_file, merge_into_scene=True, import_into_object_subnet=True)",
            "if root is None:",
            "    raise RuntimeError(f'FBX import returned null root: {fbx_file}')",
            "def _find_geo(root_node, preferred_name):",
            "    if preferred_name:",
            "        cand = root_node.node(preferred_name)",
            "        if cand is not None and cand.type().name() == 'geo':",
            "            return cand",
            "    for child in root_node.children():",
            "        if child.type().name() == 'geo':",
            "            return child",
            "    for child in root_node.allSubChildren():",
            "        if child.type().name() == 'geo':",
            "            return child",
            "    return None",
            "geo = _find_geo(root, preferred_geo_obj)",
            "if geo is None:",
            "    raise RuntimeError(f'No geo object found in FBX import root: {root.path()}')",
            "sop = geo.displayNode() or geo.renderNode() or (geo.children()[-1] if geo.children() else None)",
            "if sop is None:",
            "    raise RuntimeError(f'No SOP output found for geo object: {geo.path()}')",
            "export_sop = sop",
            "if track_sop_name:",
            "    obj = hou.node('/obj')",
            "    export_geo = obj.createNode('geo', 'hou2ue_fbx_export_geo')",
            "    for child in list(export_geo.children()):",
            "        child.destroy()",
            "    merge = export_geo.createNode('object_merge', 'in_src')",
            "    merge.parm('objpath1').set(sop.path())",
            "    merge.parm('xformtype').set(1)",
            "    export_sop = merge",
            "    if strip_prim_name_attrs:",
            "        cleanup = export_geo.createNode('attribdelete', track_sop_name)",
            "        cleanup.setInput(0, export_sop)",
            "        cleanup.parm('primdel').set('name path shop_materialpath')",
            "        cleanup.parm('ptdel').set('')",
            "        cleanup.parm('vtxdel').set('')",
            "        cleanup.parm('dtldel').set('')",
            "        export_sop = cleanup",
            "    else:",
            "        rename = export_geo.createNode('null', track_sop_name)",
            "        rename.setInput(0, export_sop)",
            "        export_sop = rename",
            "    export_sop.setDisplayFlag(True)",
            "    export_sop.setRenderFlag(True)",
            "outnet = hou.node('/out')",
            "rop = outnet.createNode('alembic', 'hou2ue_nnm_export_rop')",
            "rop.parm('use_sop_path').set(1)",
            "rop.parm('sop_path').set(export_sop.path())",
            "rop.parm('filename').set(output_abc)",
            "rop.parm('mkpath').set(1)",
            "rop.render(frame_range=(frame_start, frame_end, 1), verbose=False)",
            "print(geo.path())",
            "print(sop.path())",
            "print(export_sop.path())",
            "print(output_abc)",
        ]
    )

    result = subprocess.run(
        [str(hython), "-"],
        input=script,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "hython FBX->Alembic export failed. "
            f"fbx={fbx_file}\nstdout={result.stdout}\nstderr={result.stderr}"
        )
    if not output_abc.exists():
        raise RuntimeError(
            "hython FBX->Alembic export finished without output file. "
            f"fbx={fbx_file}\nstdout={result.stdout}\nstderr={result.stderr}"
        )

    return {
        "fbx_source": str(fbx_file.resolve()),
        "output_abc": str(output_abc.resolve()),
        "frame_start": int(frame_start),
        "frame_end": int(frame_end),
        "track_sop_name": str(track_sop_name),
        "strip_prim_name_attrs": bool(strip_prim_name_attrs),
        "stdout_tail": result.stdout[-4000:],
        "stderr_tail": result.stderr[-4000:],
    }


def _export_nnm_geom_caches(
    cfg: Dict[str, Any],
    profile: str,
    run_dir: Path,
    export_dir: Path,
    hython: Path,
) -> Dict[str, Any]:
    ue_cfg = require_nested(cfg, ("ue",))
    dynamic_cfg = require_nested(ue_cfg, ("dynamic_assets",))
    source_cfg = ue_cfg.get("nnm_geomcache_sources", {})
    if not isinstance(source_cfg, dict) or not source_cfg:
        return {}

    art_root = Path(require_nested(cfg, ("paths", "art_source_root")))
    exports: Dict[str, Any] = {}

    key_to_template = {
        "upper": str(dynamic_cfg.get("nnm_upper_geom_cache_destination_template", "")),
        "lower": str(dynamic_cfg.get("nnm_lower_geom_cache_destination_template", "")),
    }

    for key in ("upper", "lower"):
        part_cfg = source_cfg.get(key)
        if not isinstance(part_cfg, dict):
            continue

        dst_template = key_to_template.get(key, "")
        if not dst_template:
            continue

        source_rel = str(part_cfg.get("source_rel", "") or "").strip()
        if not source_rel:
            raise RuntimeError(f"nnm_geomcache_sources.{key}.source_rel is empty")

        source_path = art_root / source_rel
        if not source_path.exists():
            raise RuntimeError(f"NNM geom cache source FBX does not exist: {source_path}")

        preferred_geo_obj = str(part_cfg.get("preferred_geo_obj", "") or "")
        frame_start = int(part_cfg.get("frame_start", 1))
        frame_end = int(part_cfg.get("frame_end", 240))

        dst_asset = apply_template(dst_template, profile, run_dir)
        asset_name = dst_asset.rsplit("/", 1)[-1]
        output_abc = export_dir / f"{asset_name}.abc"

        exports[key] = _run_hython_fbx_to_abc_export(
            hython=hython,
            fbx_file=source_path,
            output_abc=output_abc,
            preferred_geo_obj=preferred_geo_obj,
            frame_start=frame_start,
            frame_end=frame_end,
        )
        exports[key]["destination_asset"] = dst_asset

    return exports


def _resolve_flesh_source(
    cfg: Dict[str, Any],
    pose_frames: List[int],
) -> Dict[str, Any]:
    ue_cfg = require_nested(cfg, ("ue",))
    source_cfg = ue_cfg.get("flesh_geomcache_source", {})
    if not isinstance(source_cfg, dict):
        source_cfg = {}

    mode = str(source_cfg.get("mode", "pdg_bgeo") or "pdg_bgeo").strip().lower()
    if mode not in {"pdg_bgeo", "fbx_anim"}:
        raise RuntimeError(f"Unsupported ue.flesh_geomcache_source.mode: {mode}")

    if mode == "pdg_bgeo":
        return {"mode": mode}

    art_root = Path(require_nested(cfg, ("paths", "art_source_root")))
    source_rel = str(require_nested(source_cfg, ("source_rel",)))
    source_fbx = art_root / source_rel
    if not source_fbx.exists():
        raise RuntimeError(f"Flesh FBX source does not exist: {source_fbx}")

    frame_start = int(source_cfg.get("frame_start", 1))
    expected = len(pose_frames)
    default_end = frame_start if expected <= 0 else (frame_start + expected - 1)
    frame_end = int(source_cfg.get("frame_end", default_end))
    if frame_end < frame_start:
        frame_end = frame_start

    return {
        "mode": mode,
        "source_fbx": source_fbx,
        "preferred_geo_obj": str(source_cfg.get("preferred_geo_obj", "") or ""),
        "track_sop_name": str(source_cfg.get("track_sop_name", "body_mesh") or "body_mesh"),
        "frame_start": frame_start,
        "frame_end": frame_end,
    }


def _load_selected_tissue_files(run_manifest: Dict[str, Any]) -> List[Path]:
    selected = (
        run_manifest.get("selected_outputs", {}).get("tissue_training_files", [])
        if isinstance(run_manifest.get("selected_outputs"), dict)
        else []
    )
    out: List[Path] = []
    for raw in selected:
        p = Path(str(raw))
        if p.exists():
            out.append(p)
    if out:
        return _sorted_by_index(out)

    # Backward-compatible fallback for old manifests.
    out_prefix = str(run_manifest.get("out_prefix", ""))
    output_root = Path(str(run_manifest.get("output_root", "")))
    tissue_mesh = [
        p
        for p in output_root.rglob("*")
        if p.is_file() and f"{out_prefix}_ML_PDG_tissue_mesh" in f"{p.parent.as_posix()}/{p.name}"
    ]
    if tissue_mesh:
        return _sorted_by_index(tissue_mesh)

    tissue_sim = [
        p
        for p in output_root.rglob("*")
        if p.is_file() and f"{out_prefix}_ML_PDG_tissue_sim" in f"{p.parent.as_posix()}/{p.name}"
    ]
    return _sorted_by_index(tissue_sim)


def _load_selected_muscle_files(run_manifest: Dict[str, Any]) -> List[Path]:
    selected = (
        run_manifest.get("selected_outputs", {}).get("muscle_debug_files", [])
        if isinstance(run_manifest.get("selected_outputs"), dict)
        else []
    )
    out: List[Path] = []
    for raw in selected:
        p = Path(str(raw))
        if p.exists():
            out.append(p)
    return _sorted_by_index(out)


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir)
    report_path = stage_report_path(run_dir, "convert")
    report = make_report(
        stage="convert",
        profile=args.profile,
        inputs={
            "config": str(Path(args.config).resolve()),
            "run_dir": str(run_dir.resolve()),
            "profile": args.profile,
        },
    )

    try:
        cfg = load_config(args.config)
        run_manifest_path = run_dir / "manifests" / "run_manifest.json"
        if not run_manifest_path.exists():
            raise RuntimeError(f"Missing run_manifest.json: {run_manifest_path}")

        run_manifest = load_json(run_manifest_path)
        pose_frames = [int(v) for v in run_manifest["pose_frames"]]
        muscle_files = _load_selected_muscle_files(run_manifest)
        flesh_source = _resolve_flesh_source(cfg, pose_frames)

        expected = len(pose_frames)

        export_dir = run_dir / "workspace" / "staging" / args.profile / "houdini_exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        stitched_abc = export_dir / f"GC_upperBodyFlesh_{args.profile}.abc"
        hython = _find_hython(cfg)

        flesh_source_mode = str(flesh_source.get("mode", "pdg_bgeo"))
        export_log: Dict[str, Any] = {}
        pose_rows: List[Tuple[int, int, int]] = []
        source_files_for_report: List[str] = []
        tissue_count_for_report = 0

        if flesh_source_mode == "fbx_anim":
            source_fbx = Path(flesh_source["source_fbx"])
            frame_start = int(flesh_source["frame_start"])
            frame_end = int(flesh_source["frame_end"])
            if expected > 0:
                frame_end = frame_start + expected - 1

            export_log = _run_hython_fbx_to_abc_export(
                hython=hython,
                fbx_file=source_fbx,
                output_abc=stitched_abc,
                preferred_geo_obj=str(flesh_source.get("preferred_geo_obj", "")),
                frame_start=frame_start,
                frame_end=frame_end,
                track_sop_name=str(flesh_source.get("track_sop_name", "body_mesh")),
                strip_prim_name_attrs=True,
            )
            frame_count = int(frame_end - frame_start + 1)
            for sample_index in range(frame_count):
                pose_frame = pose_frames[sample_index % len(pose_frames)] if pose_frames else (sample_index + 1)
                source_frame = frame_start + sample_index
                pose_rows.append((sample_index, pose_frame, source_frame))

            export_mode = "hython_fbx_anim_to_alembic"
            source_files_for_report = [str(source_fbx.resolve())]
            tissue_count_for_report = frame_count
        else:
            tissue_files = _load_selected_tissue_files(run_manifest)
            if not tissue_files:
                raise RuntimeError("No tissue files available for Alembic conversion.")
            if expected > 0 and len(tissue_files) != expected:
                raise RuntimeError(
                    f"Tissue file count mismatch. expected={expected} got={len(tissue_files)}"
                )

            if all(str(p).lower().endswith(".abc") for p in tissue_files):
                if len(tissue_files) == 1:
                    shutil.copy2(tissue_files[0], stitched_abc)
                    export_mode = "copy_single_abc"
                else:
                    raise RuntimeError(
                        "Multiple Alembic inputs are not supported by current export path. "
                        "Provide bgeo sequence inputs or a single abc."
                    )
            else:
                seq_dir = export_dir / "_tmp_bgeo_sequence"
                seq_pattern, frame_count = _build_sequence_files(tissue_files, seq_dir)
                export_log = _run_hython_abc_export(
                    hython=hython,
                    seq_pattern=seq_pattern,
                    frame_count=frame_count,
                    output_abc=stitched_abc,
                )
                export_mode = "hython_alembic_rop"

            for sample_index, src_path in enumerate(tissue_files):
                pose_frame = pose_frames[sample_index % len(pose_frames)] if pose_frames else (sample_index + 1)
                source_frame = _extract_source_frame(src_path)
                pose_rows.append((sample_index, pose_frame, source_frame))

            source_files_for_report = [str(p.resolve()) for p in tissue_files]
            tissue_count_for_report = len(tissue_files)

        pose_map_csv = export_dir / "pose_frame_map.csv"
        with pose_map_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["sample_index", "poseFrame", "source_frame"])
            for sample_index, pose_frame, source_frame in pose_rows:
                writer.writerow([sample_index, pose_frame, source_frame])

        debug_dir = export_dir / "debug_muscle_mesh"
        debug_dir.mkdir(parents=True, exist_ok=True)
        for src in muscle_files:
            dst = debug_dir / src.name
            if not dst.exists():
                shutil.copy2(src, dst)

        nnm_exports = _export_nnm_geom_caches(
            cfg=cfg,
            profile=args.profile,
            run_dir=run_dir,
            export_dir=export_dir,
            hython=hython,
        )

        finalize_report(
            report,
            status="success",
            outputs={
                "stitched_abc": str(stitched_abc.resolve()),
                "pose_frame_map_csv": str(pose_map_csv.resolve()),
                "debug_muscle_dir": str(debug_dir.resolve()),
                "tissue_count": tissue_count_for_report,
                "muscle_count": len(muscle_files),
                "export_mode": export_mode,
                "flesh_source_mode": flesh_source_mode,
                "hython": str(hython.resolve()),
                "source_files": source_files_for_report,
                "export_log": export_log,
                "nnm_geom_cache_exports": nnm_exports,
            },
            errors=[],
        )
        write_json(report_path, report)
        return 0

    except (ConfigError, RuntimeError, Exception) as exc:
        finalize_report(
            report,
            status="failed",
            outputs={},
            errors=[
                {
                    "message": str(exc),
                    "traceback": traceback.format_exc(),
                }
            ],
        )
        write_json(report_path, report)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
