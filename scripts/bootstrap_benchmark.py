from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, default=ROOT / "vendor" / "BugsInPy")
    parser.add_argument("--project", default="PySnooper")
    parser.add_argument("--bug", default="1")
    parser.add_argument("--root", type=Path, default=ROOT / "workspace")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    framework = args.benchmark / "framework" / "bin"
    args.root.mkdir(parents=True, exist_ok=True)
    records = []
    for version, label in [(0, "buggy"), (1, "fixed")]:
        destination = args.root / f"harness-pysnooper-{label}"
        if not (destination / args.project).exists():
            subprocess.run(["bash", str(framework / "bugsinpy-checkout"), "-p", args.project, "-i", args.bug, "-v", str(version), "-w", str(destination)], check=True)
        records.append({"label": label, "path": str(destination / args.project), "version": version})
    result = {"source": "https://github.com/soarsmu/BugsInPy", "project": args.project, "bug": args.bug, "checkouts": records}
    (ROOT / "artifacts" / "harness").mkdir(parents=True, exist_ok=True)
    (ROOT / "artifacts" / "harness" / "bootstrap_checkouts.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
