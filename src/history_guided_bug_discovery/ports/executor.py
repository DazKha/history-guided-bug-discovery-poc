from typing import Protocol

from ..domain.models import ExecutionRequest, ExecutionResult


class TestExecutor(Protocol):
    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        ...
