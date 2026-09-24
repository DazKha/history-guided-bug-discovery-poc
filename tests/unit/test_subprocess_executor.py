import sys
from pathlib import Path

import pytest

from history_guided_bug_discovery.adapters import subprocess_executor as module
from history_guided_bug_discovery.adapters.subprocess_executor import SubprocessExecutor
from history_guided_bug_discovery.domain.enums import Arm
from history_guided_bug_discovery.domain.models import ExecutionRequest, TestArtifact as DomainTestArtifact


def artifact(artifact_id="safe", code="def test_ok():\n    assert True\n"):
    value = DomainTestArtifact.create("run", artifact_id, "h1", Arm.DIRECT, code, "prompt", ())
    return value


def request(checkout: Path, value: DomainTestArtifact, executable=sys.executable):
    return ExecutionRequest("run", "request", "target", checkout, value, (executable, "-m", "pytest", "-q"), {}, 1, "pytest")


def test_unsafe_artifact_id_cannot_escape_checkout_and_collision_is_preserved(tmp_path):
    existing = tmp_path / "_generated_eval_existing.py"
    existing.write_text("sentinel", encoding="utf-8")
    result = SubprocessExecutor().execute(request(tmp_path, artifact("../../existing")))
    assert result.command[-1] != existing.name
    assert existing.read_text(encoding="utf-8") == "sentinel"
    assert list(tmp_path.glob("_generated_eval_*.py")) == [existing]


def test_cleanup_after_execution_exception(tmp_path, monkeypatch):
    def explode(*args, **kwargs):
        injected = Path(kwargs["cwd"]) / args[0][-1]
        assert injected.exists()
        raise RuntimeError("runner exploded")

    monkeypatch.setattr(module.subprocess, "run", explode)
    with pytest.raises(RuntimeError, match="runner exploded"):
        SubprocessExecutor().execute(request(tmp_path, artifact("exception")))
    assert not list(tmp_path.glob("_generated_eval_*.py"))


def test_missing_checkout_and_interpreter_fail_before_execution(tmp_path):
    with pytest.raises(FileNotFoundError, match="checkout"):
        SubprocessExecutor().execute(request(tmp_path / "missing", artifact()))
    with pytest.raises(FileNotFoundError, match="interpreter"):
        SubprocessExecutor().execute(request(tmp_path, artifact(), executable="definitely-not-a-python"))
