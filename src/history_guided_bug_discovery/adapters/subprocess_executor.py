from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from ..domain.enums import ExecutionState, FailureType
from ..domain.models import ExecutionRequest, ExecutionResult, stable_hash


_MECHANICAL_MARKERS = ("modulenotfounderror", "importerror", "syntaxerror", "filenotfounderror", "error during collection", "no such file or directory", "fixture .* not found")


def _normalize(output: str) -> str:
    return "\n".join(line.rstrip() for line in output.splitlines()) + "\n"


class SubprocessExecutor:
    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        started = time.monotonic()
        checkout = Path(request.target_checkout)
        if not checkout.is_dir():
            raise FileNotFoundError(f"checkout is unavailable: {checkout}")
        if not request.command:
            raise FileNotFoundError("interpreter is unavailable: command is empty")
        interpreter = str(request.command[0])
        interpreter_path = Path(interpreter)
        if interpreter_path.is_absolute():
            available = interpreter_path.is_file() and os.access(interpreter_path, os.X_OK)
        else:
            available = shutil.which(interpreter, path=os.environ.get("PATH")) is not None
        if not available:
            raise FileNotFoundError(f"interpreter is unavailable: {interpreter}")
        if stable_hash(request.test_artifact.code) != request.test_artifact.test_sha256:
            raise ValueError(f"test content hash mismatch: {request.test_artifact.artifact_id}")
        injected: Path | None = None
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".py", prefix="_generated_eval_", dir=checkout, delete=False) as handle:
            injected = Path(handle.name)
            handle.write(request.test_artifact.code + ("\n" if not request.test_artifact.code.endswith("\n") else ""))
        environment = os.environ.copy()
        environment.update(dict(request.environment))
        environment.setdefault("PYTHONPATH", str(checkout))
        command = (*request.command, injected.name)
        try:
            completed = subprocess.run(command, cwd=checkout, env=environment, capture_output=True, text=True, timeout=request.timeout_seconds, shell=False)
            stdout = completed.stdout or ""
            stderr = completed.stderr or ""
            normalized = _normalize(stdout + stderr)
            lower = normalized.lower()
            if completed.returncode == 0:
                state, failure = ExecutionState.PASS, FailureType.NONE
            elif any(re.search(marker, lower) for marker in _MECHANICAL_MARKERS) or "assert false" in lower or "pytest.fail" in lower:
                state, failure = ExecutionState.MECHANICAL_FAILURE, FailureType.MECHANICAL_FAILURE
            elif "assertionerror" in lower or re.search(r"\bassert\b", lower):
                state, failure = ExecutionState.FAIL, FailureType.ASSERTION_FAILURE
            else:
                state, failure = ExecutionState.FAIL, FailureType.TARGET_EXCEPTION
            return ExecutionResult(request.run_id, request.request_id, request.target_id, state, failure, completed.returncode, stdout, stderr, normalized, _exception_type(normalized), command, round(time.monotonic() - started, 3))
        except subprocess.TimeoutExpired as exc:
            stdout = _decode(exc.stdout)
            stderr = _decode(exc.stderr)
            normalized = _normalize(stdout + stderr + "\nTIMEOUT\n")
            return ExecutionResult(request.run_id, request.request_id, request.target_id, ExecutionState.TIMEOUT, FailureType.MECHANICAL_FAILURE, 124, stdout, stderr, normalized, "TimeoutExpired", command, round(time.monotonic() - started, 3))
        finally:
            try:
                if injected is not None:
                    injected.unlink(missing_ok=True)
            except OSError:
                pass


def _decode(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _exception_type(output: str) -> str:
    matches = re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception))\b", output)
    return matches[-1] if matches else ""
