#!/usr/bin/env python3
import datetime as dt
import json
import pathlib
import subprocess

import yaml


def git(args, cwd):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def main() -> int:
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    third_party = repo_root / "prototype" / "third_party"
    lock_path = repo_root / "prototype" / "config" / "repos.lock.yaml"

    notes_map = {
        "neural-blend-shapes": "NMM-related baseline and blendshape learning reference.",
        "DeePSD": "Pose-space deformation prior.",
        "PBNS": "Pose-driven blendshape style baseline.",
        "NeuralClothSim": "Cloth deformation reference for costume-like behavior.",
        "fast-snarf": "Dynamic registration/binding related reference.",
        "NeuralHaircut": "Groom/hair reconstruction and rendering reference.",
    }

    repos = []
    for child in sorted(third_party.iterdir()):
        if not child.is_dir():
            continue
        if not (child / ".git").exists():
            continue

        try:
            url = git(["-C", str(child), "remote", "get-url", "origin"], cwd=repo_root)
            commit = git(["-C", str(child), "rev-parse", "HEAD"], cwd=repo_root)
            branch = git(["-C", str(child), "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root)
        except subprocess.CalledProcessError:
            continue

        repos.append(
            {
                "name": child.name,
                "repo_url": url,
                "branch": branch,
                "commit": commit,
                "subdir": str((pathlib.Path("prototype") / "third_party" / child.name).as_posix()),
                "license": "See upstream LICENSE",
                "notes": notes_map.get(child.name, "Upstream reference repo."),
            }
        )

    payload = {
        "version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repos": repos,
    }

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, allow_unicode=True, sort_keys=False)

    print(json.dumps({"repos": len(repos), "lock_path": str(lock_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
