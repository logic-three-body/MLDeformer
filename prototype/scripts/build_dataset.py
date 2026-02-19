#!/usr/bin/env python3
import argparse
import datetime as dt
import hashlib
import json
import pathlib

import yaml

VALID_EXT = {
    ".obj": "mesh",
    ".fbx": "mesh",
    ".ply": "mesh",
    ".abc": "groom",
    ".usd": "mesh",
    ".usda": "mesh",
    ".gltf": "animation",
    ".glb": "animation",
    ".bvh": "animation",
    ".json": "meta",
}


def hash_prefix(path: pathlib.Path, limit: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    remaining = limit
    with path.open("rb") as f:
        while remaining > 0:
            chunk = f.read(min(1024 * 1024, remaining))
            if not chunk:
                break
            h.update(chunk)
            remaining -= len(chunk)
    return h.hexdigest()


def split_for_hash(h: str) -> str:
    v = int(h[:8], 16) % 10
    if v < 8:
        return "train"
    if v == 8:
        return "val"
    return "test"


def load_manifest(path: pathlib.Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def guess_source_asset(file_path: pathlib.Path, assets: list[dict]) -> str:
    fp = str(file_path).replace("\\", "/").lower()
    for asset in assets:
        target = str(asset.get("target_path", "")).replace("\\", "/").lower()
        if target and target in fp:
            return asset.get("asset_id", "unknown")
    return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build dataset manifest and run basic QC")
    parser.add_argument("--data-root", default="D:/MLDPrototypeData")
    parser.add_argument("--manifest", default="prototype/config/assets.manifest.yaml")
    parser.add_argument("--out", default="processed/dataset_manifest.jsonl")
    args = parser.parse_args()

    data_root = pathlib.Path(args.data_root)
    raw_root = data_root / "raw"
    out_path = data_root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest(pathlib.Path(args.manifest))
    assets = manifest.get("assets", [])

    files = [p for p in raw_root.rglob("*") if p.is_file() and p.suffix.lower() in VALID_EXT]
    records = []
    for idx, file_path in enumerate(sorted(files)):
        topology_hash = hash_prefix(file_path)
        modality = VALID_EXT[file_path.suffix.lower()]
        qc_status = "passed" if file_path.stat().st_size > 0 else "failed_empty"
        rec = {
            "sample_id": f"sample_{idx:06d}",
            "split": split_for_hash(topology_hash),
            "mesh_topology_hash": topology_hash,
            "frame_range": "0-0",
            "modality": modality,
            "source_asset": guess_source_asset(file_path, assets),
            "qc_status": qc_status,
            "relative_path": str(file_path.relative_to(data_root)).replace("\\", "/"),
        }
        records.append(rec)

    with out_path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    summary = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "data_root": str(data_root),
        "raw_file_count": len(files),
        "record_count": len(records),
        "output": str(out_path),
    }
    summary_path = out_path.with_name("dataset_summary.json")
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
