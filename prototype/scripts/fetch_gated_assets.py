#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import pathlib
import urllib.request

import yaml


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


def download_with_token(url: str, token: str, target: pathlib.Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    tmp = target.with_suffix(target.suffix + ".part")
    with urllib.request.urlopen(req, timeout=120) as resp, tmp.open("wb") as out:
        out.write(resp.read())
    tmp.replace(target)


def resolve_token(auth_mode: str) -> str:
    if auth_mode.startswith("env:"):
        return os.getenv(auth_mode.split(":", 1)[1], "")
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch gated assets with manual fallback")
    parser.add_argument("--manifest", default="prototype/config/assets.manifest.yaml")
    parser.add_argument("--data-root", default="D:/MLDPrototypeData")
    parser.add_argument("--state", default="prototype/state/assets_status.json")
    args = parser.parse_args()

    manifest = load_manifest(pathlib.Path(args.manifest))
    state_path = pathlib.Path(args.state)
    state = load_state(state_path)
    data_root = pathlib.Path(args.data_root)
    data_root.mkdir(parents=True, exist_ok=True)

    for asset in manifest.get("assets", []):
        if not asset.get("gated", False):
            continue

        asset_id = asset.get("asset_id", "unknown")
        auth_mode = str(asset.get("auth_mode", "manual"))
        url = ((asset.get("download") or {}).get("url") or "").strip()
        target_path = data_root / asset.get("target_path", f"raw/gated/{asset_id}")

        result = {
            "asset_id": asset_id,
            "gated": True,
            "target_path": str(target_path),
            "auth_mode": auth_mode,
            "status": "manual_pending",
            "message": "",
        }

        if target_path.exists() and ((target_path.is_dir() and any(target_path.iterdir())) or target_path.is_file()):
            result["status"] = "ready"
            result["message"] = "already_exists"
            state["assets"][asset_id] = result
            print(f"[{asset_id}] ready - already_exists")
            continue

        if auth_mode.startswith("manual:"):
            result["status"] = "manual_pending"
            result["message"] = f"requires_manual_action:{auth_mode.split(':', 1)[1]}"
        elif auth_mode.startswith("env:"):
            token = resolve_token(auth_mode)
            if not token:
                result["status"] = "manual_pending"
                result["message"] = f"missing_credential_env:{auth_mode.split(':', 1)[1]}"
            elif not url:
                result["status"] = "manual_pending"
                result["message"] = "missing_download_url"
            else:
                try:
                    download_with_token(url, token, target_path)
                    result["status"] = "ready"
                    result["message"] = "downloaded_with_token"
                except Exception as exc:
                    result["status"] = "failed"
                    result["message"] = str(exc)
        else:
            result["status"] = "manual_pending"
            result["message"] = f"unknown_auth_mode:{auth_mode}"

        state["assets"][asset_id] = result
        print(f"[{asset_id}] {result['status']} - {result['message']}")

    save_state(state_path, state)
    print(f"State saved: {state_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
