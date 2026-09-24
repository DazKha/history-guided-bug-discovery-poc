from __future__ import annotations

from pathlib import Path

from ..domain.models import TargetContext, TargetSpec, TestArtifact
from ..ports.target import PreparedTarget, TargetAdapter, TestRunner


class BugsInPyTargetAdapter:
    def __init__(self, context_path: str | Path, visible_files: tuple[str, ...] = (), python_executable: str = "python3", runner: str = "pytest"):
        self.context_path = Path(context_path)
        self.visible_files = tuple(visible_files)
        self.python_executable = python_executable
        self.runner = runner

    def prepare(self, target: TargetSpec) -> PreparedTarget:
        checkout = Path(target.buggy_checkout)
        if not checkout.exists():
            raise FileNotFoundError(f"buggy checkout does not exist: {checkout}")
        executable = Path(self.python_executable)
        if not executable.is_absolute():
            candidate = checkout / executable
            if candidate.exists():
                self.python_executable = str(candidate)
        return PreparedTarget(target, checkout)

    def build_context(self, target: PreparedTarget) -> TargetContext:
        return TargetContext.create(target.spec.run_id, target.spec.target_id, self.context_path.read_text(encoding="utf-8"), self.visible_files or (str(self.context_path),))

    def select_runner(self, test: TestArtifact) -> TestRunner:
        return TestRunner(self.python_executable, ("-m", self.runner, "-q"))
