from __future__ import annotations

"""Target-neutral candidate execution used only by Experiment 5 evaluators."""

import ast
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / "workspace/harness-pysnooper-buggy/PySnooper/env39/bin/python"


def _needs_unittest(source: str) -> bool:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases = [ast.unparse(base) if hasattr(ast, "unparse") else getattr(base, "id", "") for base in node.bases]
            if any(token in " ".join(bases) for token in ("TestCase", "AsyncTestCase", "AsyncHTTPTestCase")):
                return True
    return False


def run_test(repo: Path, test_source: Path, log_path: Path) -> tuple[int, str, str]:
    test_name = f"_generated_eval_{test_source.stem}.py"
    injected = repo / test_name
    source = test_source.read_text()
    shutil.copyfile(test_source, injected)
    python = PYTHON if PYTHON.exists() else Path("python3")
    env = os.environ.copy()
    env.update({"LC_ALL": "C", "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0", "PYTHONPATH": str(repo)})
    runner = "unittest" if _needs_unittest(source) else "pytest"
    command = [str(python), "-m", runner, "-q", test_name]
    try:
        completed = subprocess.run(command, cwd=repo, env=env, capture_output=True, text=True, timeout=90)
        output = (completed.stdout or "") + (completed.stderr or "")
        output = "\n".join(line.rstrip() for line in output.splitlines()) + "\n"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(output)
        return completed.returncode, output, runner
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        output = stdout + stderr + "\nTIMEOUT\n"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(output)
        return 124, output, runner
    finally:
        injected.unlink(missing_ok=True)
