from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(repo: Path) -> dict:
    env = os.environ.copy()
    env.update({"LC_ALL": "C", "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0", "PYTHONPATH": str(repo)})
    command = [str(repo / "env39" / "bin" / "python"), "-m", "pytest", "-q", "-s", "tests/test_chinese.py::test_chinese"]
    completed = subprocess.run(command, cwd=repo, env=env, capture_output=True, text=True, timeout=90)
    return {"command": command, "cwd": str(repo), "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}


def main() -> None:
    buggy = ROOT / "workspace" / "harness-pysnooper-buggy" / "PySnooper"
    fixed = ROOT / "workspace" / "harness-pysnooper-fixed" / "PySnooper"
    results = {"buggy": run(buggy), "fixed": run(fixed)}
    harness_dir = ROOT / "artifacts" / "harness"
    harness_dir.mkdir(parents=True, exist_ok=True)
    for label, result in results.items():
        (harness_dir / f"{label}_regression.log").write_text(result["stdout"] + result["stderr"])
    versions = {
        "python": sys.version,
        "platform": platform.platform(),
        "git": subprocess.run(["git", "--version"], capture_output=True, text=True, check=True).stdout.strip(),
        "docker": subprocess.run(["docker", "--version"], capture_output=True, text=True, check=True).stdout.strip(),
        "bugsinpy_revision": subprocess.run(["git", "-C", str(ROOT / "vendor" / "BugsInPy"), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip(),
    }
    (harness_dir / "environment.json").write_text(json.dumps(versions, indent=2) + "\n")
    (harness_dir / "verification.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps({label: result["returncode"] for label, result in results.items()}))


if __name__ == "__main__":
    main()
