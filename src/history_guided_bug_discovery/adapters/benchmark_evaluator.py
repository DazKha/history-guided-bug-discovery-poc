from __future__ import annotations

import re
from typing import Any, Mapping

from ..domain.enums import FailureCategory, PairClassification
from ..domain.models import EvaluationResult, FrozenHypothesis, PairExecutionResult


class BenchmarkEvaluator:
    """Evaluator-only adapter preserving the Experiment 2/4 F2P semantics."""

    version = "benchmark_f2p_v1"

    def __init__(self, source_path_markers: tuple[str, ...] = ("pysnooper/", "pysnooper\\", "tracer.py", "workspace/harness")):
        self.source_path_markers = tuple(marker.lower() for marker in source_path_markers)

    def evaluate(self, hypothesis: FrozenHypothesis, pair: PairExecutionResult) -> EvaluationResult:
        oracle_supported = self._oracle_supported(hypothesis)
        buggy = self._normalized_result(hypothesis, pair.buggy)
        fixed = self._normalized_result(hypothesis, pair.fixed)
        if not oracle_supported:
            classification = PairClassification.UNSUPPORTED_ORACLE
            category = FailureCategory.UNSUPPORTED_ORACLE
        elif buggy.state.value in {"MECHANICAL_FAILURE", "TIMEOUT"} or fixed.state.value in {"MECHANICAL_FAILURE", "TIMEOUT"}:
            classification = PairClassification.MECHANICAL_FAILURE
            category = FailureCategory.MECHANICAL_FAILURE
        elif buggy.state.value == "FAIL" and fixed.state.value == "PASS":
            classification = PairClassification.F2P
            category = FailureCategory.VALID_EXCEPTION_F2P if buggy.failure_type.value == "TARGET_EXCEPTION" else FailureCategory.VALID_ASSERTION_F2P
        elif buggy.state.value == "PASS" and fixed.state.value == "PASS":
            classification = PairClassification.P2P
            category = FailureCategory.TRIGGER_TOO_WEAK
        elif buggy.state.value == "FAIL" and fixed.state.value == "FAIL":
            classification = PairClassification.F2F
            category = FailureCategory.SEMANTIC_NON_TRIGGER
        elif buggy.state.value == "PASS" and fixed.state.value == "FAIL":
            classification = PairClassification.P2F
            category = FailureCategory.SEMANTIC_NON_TRIGGER
        else:
            classification = PairClassification.MECHANICAL_FAILURE
            category = FailureCategory.MECHANICAL_FAILURE
        return EvaluationResult(pair.run_id, pair.pair_id, hypothesis.hypothesis_id, pair.test_artifact_id, classification, category, classification is PairClassification.F2P and pair.same_test and oracle_supported, oracle_supported, "ACTIVATED" if buggy.state.value == "FAIL" else "NOT_ACTIVATED", self.version, {"buggy_failure_type": buggy.failure_type.value, "fixed_failure_type": fixed.failure_type.value, "buggy_exception": buggy.exception, "fixed_exception": fixed.exception})

    def _normalized_result(self, hypothesis: FrozenHypothesis, result):
        if result.failure_type.value != "TARGET_EXCEPTION":
            return result
        text = result.normalized_log.lower()
        claim = " ".join([hypothesis.claim, hypothesis.trigger, hypothesis.potential_failure, *(str(value) for value in hypothesis.oracle.values())]).lower()
        relevant_path = any(marker in text for marker in self.source_path_markers)
        relevant_exception = bool(result.exception and result.exception.lower() in claim) or any(token in claim for token in ("encoding", "unicode", "locale"))
        if relevant_path and relevant_exception:
            return result
        from ..domain.enums import ExecutionState, FailureType
        return result.__class__(result.run_id, result.request_id, result.target_id, ExecutionState.MECHANICAL_FAILURE, FailureType.MECHANICAL_FAILURE, result.exit_code, result.stdout, result.stderr, result.normalized_log, result.exception, result.command, result.duration_seconds, result.schema_version)

    def _oracle_supported(self, hypothesis: FrozenHypothesis) -> bool:
        oracle = hypothesis.oracle or {}
        expected = str(oracle.get("expected_behavior", "")).strip()
        target = str(oracle.get("target_evidence", "")).strip()
        joined = f"{expected} {target}".lower()
        return bool(expected and target) and not any(marker in joined for marker in ("after seeing the failure", "post-hoc", "post hoc"))


class FindingValidator:
    """Minimal product-side validator; it does not require a fixed checkout."""

    def validate(self, hypothesis: FrozenHypothesis, execution: PairExecutionResult) -> bool:
        return execution.buggy.state.value == "FAIL" and bool(hypothesis.oracle)
