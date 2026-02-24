#!/usr/bin/env python3
"""Compare reference vs source Main_Sequence captures and enforce strict image thresholds."""

from __future__ import annotations

import argparse
import json
import math
import traceback
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from PIL import Image

from common import finalize_report, load_config, make_report, require_nested, stage_report_path, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare GT image sequences")
    parser.add_argument("--config", required=True)
    parser.add_argument("--profile", required=True, choices=["smoke", "full"])
    parser.add_argument("--run-dir", required=True)
    return parser.parse_args()


def _load_gray(path: Path) -> np.ndarray:
    with Image.open(path) as img:
        return np.asarray(img.convert("L"), dtype=np.float32)


def _ssim_global(x: np.ndarray, y: np.ndarray) -> float:
    c1 = (0.01 * 255.0) ** 2
    c2 = (0.03 * 255.0) ** 2

    mu_x = float(np.mean(x))
    mu_y = float(np.mean(y))
    sigma_x = float(np.var(x))
    sigma_y = float(np.var(y))
    sigma_xy = float(np.mean((x - mu_x) * (y - mu_y)))

    num = (2.0 * mu_x * mu_y + c1) * (2.0 * sigma_xy + c2)
    den = (mu_x * mu_x + mu_y * mu_y + c1) * (sigma_x + sigma_y + c2)
    if den <= 1e-12:
        return 1.0
    return float(num / den)


def _psnr(x: np.ndarray, y: np.ndarray) -> float:
    mse = float(np.mean((x - y) ** 2))
    if mse <= 1e-12:
        return 99.0
    return float(20.0 * math.log10(255.0 / math.sqrt(mse)))


def _edge_iou(x: np.ndarray, y: np.ndarray) -> float:
    gx_x, gy_x = np.gradient(x)
    gx_y, gy_y = np.gradient(y)
    mag_x = np.hypot(gx_x, gy_x)
    mag_y = np.hypot(gx_y, gy_y)

    # Use a shared threshold + local dilation tolerance to absorb sub-pixel jitter from render path.
    threshold = float(np.percentile(np.concatenate([mag_x.ravel(), mag_y.ravel()]), 85.0))
    edge_x = mag_x >= max(threshold, 1e-6)
    edge_y = mag_y >= max(threshold, 1e-6)

    def _dilate(mask: np.ndarray, radius: int = 3) -> np.ndarray:
        h, w = mask.shape
        padded = np.pad(mask, radius)
        out = np.zeros_like(mask)
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                out |= padded[radius + dx : radius + dx + h, radius + dy : radius + dy + w]
        return out

    edge_x_d = _dilate(edge_x, radius=3)
    edge_y_d = _dilate(edge_y, radius=3)

    union = int(np.count_nonzero(edge_x | edge_y))
    if union == 0:
        return 1.0
    inter = int(np.count_nonzero((edge_x & edge_y_d) | (edge_y & edge_x_d)))
    return float(inter / union)


def _write_heatmap(ref_gray: np.ndarray, src_gray: np.ndarray, out_path: Path) -> str:
    diff = np.abs(ref_gray - src_gray)
    norm = np.clip(diff, 0.0, 255.0).astype(np.uint8)
    heat = np.zeros((norm.shape[0], norm.shape[1], 3), dtype=np.uint8)
    heat[..., 0] = norm
    heat[..., 1] = (norm // 4)
    heat[..., 2] = np.clip(255 - norm, 0, 255)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(heat, mode="RGB").save(out_path)
    return str(out_path.resolve())


def _collect_frames(frames_dir: Path) -> List[Path]:
    return sorted([p for p in frames_dir.rglob("*.png") if p.is_file()])


def _safe_read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _update_infer_report(
    run_dir: Path,
    compare_enabled: bool,
    compare_status: str,
    compare_report_path: Path,
    compare_metrics: Dict[str, Any],
) -> None:
    infer_path = run_dir / "reports" / "infer_report.json"
    if not infer_path.exists():
        return

    data = _safe_read_json(infer_path)
    if not isinstance(data, dict):
        return

    outputs = data.get("outputs", {})
    if not isinstance(outputs, dict):
        outputs = {}

    outputs["ground_truth_compare_enabled"] = bool(compare_enabled)
    outputs["ground_truth_compare_report"] = str(compare_report_path.resolve())
    outputs["ground_truth_compare_status"] = str(compare_status)
    outputs["ground_truth_compare_metrics"] = compare_metrics
    data["outputs"] = outputs

    errors = data.get("errors", [])
    if not isinstance(errors, list):
        errors = []

    if compare_enabled and compare_status != "success":
        data["status"] = "failed"
        marker = "ground truth compare stage failed"
        if not any(isinstance(x, dict) and x.get("message") == marker for x in errors):
            errors.append(
                {
                    "message": marker,
                    "gt_compare_report": str(compare_report_path.resolve()),
                    "ground_truth_compare_status": compare_status,
                }
            )
    data["errors"] = errors

    infer_path.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir)
    report_path = stage_report_path(run_dir, "gt_compare")
    report = make_report(
        stage="gt_compare",
        profile=args.profile,
        inputs={
            "config": str(Path(args.config).resolve()),
            "run_dir": str(run_dir.resolve()),
            "profile": args.profile,
        },
    )

    try:
        cfg = load_config(args.config)
        gt_cfg = require_nested(cfg, ("ue", "ground_truth"))

        enabled = bool(gt_cfg.get("enabled", False))
        if not enabled:
            finalize_report(
                report,
                status="success",
                outputs={"enabled": False, "skipped": True, "reason": "ue.ground_truth.enabled=false"},
                errors=[],
            )
            write_json(report_path, report)
            _update_infer_report(run_dir, False, "disabled", report_path, {})
            return 0

        compare_cfg = gt_cfg.get("compare", {}) if isinstance(gt_cfg.get("compare"), dict) else {}
        thresholds = compare_cfg.get("thresholds", {}) if isinstance(compare_cfg.get("thresholds"), dict) else {}

        ssim_mean_min = float(thresholds.get("ssim_mean_min", 0.995))
        ssim_p05_min = float(thresholds.get("ssim_p05_min", 0.985))
        psnr_mean_min = float(thresholds.get("psnr_mean_min", 35.0))
        psnr_min_min = float(thresholds.get("psnr_min_min", 30.0))
        edge_iou_mean_min = float(thresholds.get("edge_iou_mean_min", 0.97))
        fail_on_count_mismatch = bool(compare_cfg.get("fail_on_frame_count_mismatch", True))

        ref_dir = run_dir / "workspace" / "staging" / args.profile / "gt" / "reference" / "frames"
        src_dir = run_dir / "workspace" / "staging" / args.profile / "gt" / "source" / "frames"

        ref_frames = _collect_frames(ref_dir)
        src_frames = _collect_frames(src_dir)

        errors: List[Dict[str, Any]] = []
        if not ref_frames:
            errors.append({"message": "reference frame directory is empty", "path": str(ref_dir.resolve())})
        if not src_frames:
            errors.append({"message": "source frame directory is empty", "path": str(src_dir.resolve())})

        compare_count = min(len(ref_frames), len(src_frames))
        if len(ref_frames) != len(src_frames):
            mismatch = {
                "message": "frame count mismatch",
                "reference_count": len(ref_frames),
                "source_count": len(src_frames),
            }
            if fail_on_count_mismatch:
                errors.append(mismatch)
            else:
                errors.append({**mismatch, "severity": "warning"})

        rows: List[Dict[str, Any]] = []
        if not errors or (len(errors) == 1 and errors[0].get("severity") == "warning"):
            for index in range(compare_count):
                ref_path = ref_frames[index]
                src_path = src_frames[index]

                ref_gray = _load_gray(ref_path)
                src_gray = _load_gray(src_path)
                if ref_gray.shape != src_gray.shape:
                    errors.append(
                        {
                            "message": "frame resolution mismatch",
                            "frame_index": index,
                            "reference_shape": list(ref_gray.shape),
                            "source_shape": list(src_gray.shape),
                            "reference": str(ref_path),
                            "source": str(src_path),
                        }
                    )
                    continue

                ssim = _ssim_global(ref_gray, src_gray)
                psnr = _psnr(ref_gray, src_gray)
                edge_iou = _edge_iou(ref_gray, src_gray)

                rows.append(
                    {
                        "frame_index": index,
                        "reference": str(ref_path.resolve()),
                        "source": str(src_path.resolve()),
                        "ssim": ssim,
                        "psnr": psnr,
                        "edge_iou": edge_iou,
                    }
                )

        if not rows:
            status = "failed"
            metrics_summary = {}
            worst_frames: List[Dict[str, Any]] = []
            heatmaps: List[str] = []
        else:
            ssim_values = np.asarray([row["ssim"] for row in rows], dtype=np.float64)
            psnr_values = np.asarray([row["psnr"] for row in rows], dtype=np.float64)
            edge_values = np.asarray([row["edge_iou"] for row in rows], dtype=np.float64)

            metrics_summary = {
                "frame_count_compared": int(len(rows)),
                "ssim_mean": float(np.mean(ssim_values)),
                "ssim_p05": float(np.percentile(ssim_values, 5)),
                "psnr_mean": float(np.mean(psnr_values)),
                "psnr_min": float(np.min(psnr_values)),
                "edge_iou_mean": float(np.mean(edge_values)),
            }

            gate_pass = (
                metrics_summary["ssim_mean"] >= ssim_mean_min
                and metrics_summary["ssim_p05"] >= ssim_p05_min
                and metrics_summary["psnr_mean"] >= psnr_mean_min
                and metrics_summary["psnr_min"] >= psnr_min_min
                and metrics_summary["edge_iou_mean"] >= edge_iou_mean_min
            )

            if fail_on_count_mismatch and len(ref_frames) != len(src_frames):
                gate_pass = False

            # worst frames by SSIM ascending (tie-break by PSNR ascending)
            sorted_rows = sorted(rows, key=lambda r: (r["ssim"], r["psnr"]))
            worst_frames = sorted_rows[:10]

            heatmaps = []
            heatmap_root = run_dir / "workspace" / "staging" / args.profile / "gt" / "compare" / "heatmaps"
            for row in worst_frames[:5]:
                frame_index = int(row["frame_index"])
                ref_gray = _load_gray(Path(row["reference"]))
                src_gray = _load_gray(Path(row["source"]))
                heat_path = heatmap_root / f"frame_{frame_index:04d}.png"
                heatmaps.append(_write_heatmap(ref_gray, src_gray, heat_path))

            if not gate_pass:
                errors.append(
                    {
                        "message": "ground-truth metrics did not meet strict thresholds",
                        "thresholds": {
                            "ssim_mean_min": ssim_mean_min,
                            "ssim_p05_min": ssim_p05_min,
                            "psnr_mean_min": psnr_mean_min,
                            "psnr_min_min": psnr_min_min,
                            "edge_iou_mean_min": edge_iou_mean_min,
                        },
                        "metrics": metrics_summary,
                    }
                )

            status = "success" if not errors else "failed"

        outputs = {
            "enabled": True,
            "reference_frames_dir": str(ref_dir.resolve()),
            "source_frames_dir": str(src_dir.resolve()),
            "reference_frame_count": len(ref_frames),
            "source_frame_count": len(src_frames),
            "fail_on_frame_count_mismatch": fail_on_count_mismatch,
            "thresholds": {
                "ssim_mean_min": ssim_mean_min,
                "ssim_p05_min": ssim_p05_min,
                "psnr_mean_min": psnr_mean_min,
                "psnr_min_min": psnr_min_min,
                "edge_iou_mean_min": edge_iou_mean_min,
            },
            "metrics": metrics_summary,
            "worst_frames": worst_frames,
            "heatmaps": heatmaps,
        }

        finalize_report(report, status=status, outputs=outputs, errors=errors)
        write_json(report_path, report)

        _update_infer_report(
            run_dir=run_dir,
            compare_enabled=True,
            compare_status=status,
            compare_report_path=report_path,
            compare_metrics=metrics_summary,
        )

        return 0 if status == "success" else 1

    except Exception as exc:
        finalize_report(
            report,
            status="failed",
            outputs={},
            errors=[{"message": str(exc), "traceback": traceback.format_exc()}],
        )
        write_json(report_path, report)
        _update_infer_report(
            run_dir=run_dir,
            compare_enabled=True,
            compare_status="failed",
            compare_report_path=report_path,
            compare_metrics={},
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
