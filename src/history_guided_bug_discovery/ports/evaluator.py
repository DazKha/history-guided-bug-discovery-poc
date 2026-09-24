from typing import Protocol

from ..domain.models import EvaluationResult, FrozenHypothesis, PairExecutionResult


class Evaluator(Protocol):
    def evaluate(self, hypothesis: FrozenHypothesis, pair: PairExecutionResult) -> EvaluationResult:
        ...


class FindingValidator(Protocol):
    def validate(self, hypothesis: FrozenHypothesis, execution: PairExecutionResult) -> bool:
        ...
