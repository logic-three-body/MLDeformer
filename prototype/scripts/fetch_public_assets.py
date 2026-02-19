#!/usr/bin/env python3
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import urllib.request

import yaml


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(path: pathlib.Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_state(path: pathlib.Path) -> dict:
    if not path.exists():
        return {"updated_at": None, "assets": {}}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_state(path: pathlib.Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    with path.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def download_file(url: str, target: pathlib.Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".part")
    with urllib.request.urlopen(url, timeout=120) as resp, tmp.open("wb") as out:
        out.write(resp.read())
    tmp.replace(target)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch public assets from manifest")
    parser.add_argument("--manifest", default="prototype/config/assets.manifest.yaml")
    parser.add_argument("--data-root", default="D:/MLDPrototypeData")
    parser.add_argument("--state", default="prototype/state/assets_status.json")
    args = parser.parse_args()

    manifest = load_manifest(pathlib.Path(args.manifest))
    state_path = pathlib.Path(args.state)
    state = load_state(state_path)

    data_root = pathlib.Path(args.data_root)
    data_root.mkdir(parents=True, exist_ok=True)

    assets = manifest.get("assets", [])
    for asset in assets:
        asset_id = asset.get("asset_id", "unknown")
        if asset.get("gated", False):
            continue

        target_path = data_root / asset.get("target_path", "raw/public/unknown.bin")
        url = ((asset.get("download") or {}).get("url") or "").strip()
        checksum = (asset.get("checksum") or "").strip().lower()
        result = {
            "asset_id": asset_id,
            "gated": False,
            "target_path": str(target_path),
            "status": "pending",
            "message": "",
        }

        try:
            if target_path.exists():
                if checksum:
                    file_hash = sha256_file(target_path)
                    if file_hash != checksum:
                        result["status"] = "checksum_mismatch"
                        result["message"] = f"expected={checksum}, actual={file_hash}"
                    else:
                        result["status"] = "ready"
                        result["message"] = "already_exists"
                else:
                    result["status"] = "ready"
                    result["message"] = "already_exists"
            elif not url:
                result["status"] = "manual_pending"
                result["message"] = "missing_public_url"
            else:
                download_file(url, target_path)
                if checksum:
                    file_hash = sha256_file(target_path)
                    if file_hash != checksum:
                        result["status"] = "checksum_mismatch"
                        result["message"] = f"expected={checksum}, actual={file_hash}"
                    else:
                        result["status"] = "ready"
                        result["message"] = "downloaded"
                else:
                    result["status"] = "ready"
                    result["message"] = "downloaded"
        except Exception as exc:
            result["status"] = "failed"
            result["message"] = str(exc)

        state["assets"][asset_id] = result
        print(f"[{asset_id}] {result['status']} - {result['message']}")

    save_state(state_path, state)
    print(f"State saved: {state_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
