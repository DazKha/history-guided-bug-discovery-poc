from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ..domain.models import TargetContext, TargetSpec, TestArtifact


@dataclass(frozen=True)
class PreparedTarget:
    spec: TargetSpec
    checkout: Path


@dataclass(frozen=True)
class TestRunner:
    executable: str
    arguments: tuple[str, ...]

    def command(self, test_name: str) -> tuple[str, ...]:
        return (self.executable, *self.arguments, test_name)


class TargetAdapter(Protocol):
    def prepare(self, target: TargetSpec) -> PreparedTarget:
        ...

    def build_context(self, target: PreparedTarget) -> TargetContext:
        ...

    def select_runner(self, test: TestArtifact) -> TestRunner:
        ...
