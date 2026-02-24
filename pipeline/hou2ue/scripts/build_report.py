#!/usr/bin/env python3
"""Aggregate stage reports into a single pipeline report + snapshot artifacts."""

from __future__ import annotations

import argparse
import json
import shutil
import traceback
from pathlib import Path
from typing import Any, Dict, List

from common import finalize_report, load_config, make_report, stage_report_path, timestamp_compact, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build pipeline summary report")
    parser.add_argument("--config", required=True)
    parser.add_argument("--profile", required=True, choices=["smoke", "full"])
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--out-root", required=True)
    return parser.parse_args()


def _load_stage_report(path: Path) -> Dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _yaml_dump(obj: Any, indent: int = 0) -> str:
    prefix = "  " * indent
    if isinstance(obj, dict):
        lines: List[str] = []
        for key, value in obj.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.append(_yaml_dump(value, indent + 1))
            else:
                lines.append(f"{prefix}{key}: {_yaml_scalar(value)}")
        return "\n".join(lines)
    if isinstance(obj, list):
        lines = []
        for item in obj:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.append(_yaml_dump(item, indent + 1))
            else:
                lines.append(f"{prefix}- {_yaml_scalar(item)}")
        return "\n".join(lines)
    return f"{prefix}{_yaml_scalar(obj)}"


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    needs_quote = any(ch in text for ch in [":", "#", "{", "}", "[", "]", ",", " "]) or text == ""
    if needs_quote:
        text = text.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{text}"'
    return text


def _copy_latest(run_dir: Path, out_root: Path, profile: str) -> Path:
    latest_dir = out_root / "latest" / profile
    if latest_dir.exists():
        shutil.rmtree(latest_dir)
    latest_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(run_dir, latest_dir)
    return latest_dir


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir)
    out_root = Path(args.out_root)
    report_path = stage_report_path(run_dir, "report")
    stage_report = make_report(
        stage="report",
        profile=args.profile,
        inputs={
            "config": str(Path(args.config).resolve()),
            "run_dir": str(run_dir.resolve()),
            "out_root": str(out_root.resolve()),
            "profile": args.profile,
        },
    )

    try:
        cfg = load_config(args.config)
        stages = [
            "baseline_sync",
            "preflight",
            "houdini",
            "convert",
            "ue_import",
            "ue_setup",
            "train",
            "infer",
            "gt_reference_capture",
            "gt_source_capture",
            "gt_compare",
        ]
        infer_demo_path = run_dir / "reports" / "infer_demo_report.json"
        infer_demo_report = _load_stage_report(infer_demo_path)
        baseline_sync_path = run_dir / "reports" / "baseline_sync_report.json"
        gt_compare_path = run_dir / "reports" / "gt_compare_report.json"
        coord_validation_path = run_dir / "reports" / "coord_validation_report.json"
        gt_compare_report = _load_stage_report(gt_compare_path)

        stage_reports: Dict[str, Dict[str, Any] | None] = {}
        failures: List[Dict[str, Any]] = []
        for stage in stages:
            sr = _load_stage_report(stage_report_path(run_dir, stage))
            stage_reports[stage] = sr
            if sr is None:
                failures.append({"stage": stage, "message": "Missing stage report"})
                continue
            if sr.get("status") != "success":
                failures.append({"stage": stage, "message": "Stage failed", "errors": sr.get("errors", [])})

        status = "success" if not failures else "failed"

        pipeline_report = {
            "stage": "full_pipeline",
            "profile": args.profile,
            "started_at": (
                (stage_reports.get("baseline_sync") or {}).get("started_at", "")
                or (stage_reports.get("preflight") or {}).get("started_at", "")
            ),
            "ended_at": stage_report["started_at"],
            "status": status,
            "inputs": {
                "config": str(Path(args.config).resolve()),
                "run_dir": str(run_dir.resolve()),
            },
            "outputs": {
                "stage_reports": {
                    stage: str(stage_report_path(run_dir, stage).resolve())
                    for stage in stages
                },
                "stage_status": {
                    stage: (stage_reports[stage] or {}).get("status", "missing")
                    for stage in stages
                },
                "infer_demo_report": str(infer_demo_path.resolve()) if infer_demo_path.exists() else "",
                "infer_demo_status": (
                    str((infer_demo_report or {}).get("status", "missing"))
                    if infer_demo_path.exists()
                    else "missing"
                ),
                "baseline_sync_report": str(baseline_sync_path.resolve()) if baseline_sync_path.exists() else "",
                "gt_compare_report": str(gt_compare_path.resolve()) if gt_compare_path.exists() else "",
                "coord_validation_report": (
                    str(coord_validation_path.resolve()) if coord_validation_path.exists() else ""
                ),
                "gt_compare_status": (
                    str((gt_compare_report or {}).get("status", "missing"))
                    if gt_compare_path.exists()
                    else "missing"
                ),
            },
            "errors": failures,
        }

        ts = timestamp_compact()
        pipeline_report_path = run_dir / "reports" / f"pipeline_report_{ts}.json"
        write_json(pipeline_report_path, pipeline_report)
        write_json(run_dir / "reports" / "pipeline_report_latest.json", pipeline_report)

        resolved_snapshot = {
            "profile": args.profile,
            "run_dir": str(run_dir.resolve()),
            "out_root": str(out_root.resolve()),
            "config": cfg,
        }
        resolved_yaml_path = run_dir / "resolved_config.yaml"
        resolved_yaml_path.write_text(_yaml_dump(resolved_snapshot) + "\n", encoding="utf-8")

        latest_dir = _copy_latest(run_dir, out_root, args.profile)

        finalize_report(
            stage_report,
            status=status,
            outputs={
                "pipeline_report": str(pipeline_report_path.resolve()),
                "pipeline_report_latest": str((run_dir / "reports" / "pipeline_report_latest.json").resolve()),
                "resolved_config_yaml": str(resolved_yaml_path.resolve()),
                "latest_copy_dir": str(latest_dir.resolve()),
            },
            errors=failures,
        )
        write_json(report_path, stage_report)
        return 0 if status == "success" else 1

    except Exception as exc:
        finalize_report(
            stage_report,
            status="failed",
            outputs={},
            errors=[{"message": str(exc), "traceback": traceback.format_exc()}],
        )
        write_json(report_path, stage_report)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
