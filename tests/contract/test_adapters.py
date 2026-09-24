import sys
from pathlib import Path

import pytest

from history_guided_bug_discovery.adapters.benchmark_evaluator import BenchmarkEvaluator
from history_guided_bug_discovery.adapters.json_artifact_store import JsonArtifactStore
from history_guided_bug_discovery.adapters.subprocess_executor import SubprocessExecutor
from history_guided_bug_discovery.domain.enums import Arm, ExecutionState, FailureType, PairClassification, Stage
from history_guided_bug_discovery.domain.models import ExecutionRequest, ExecutionResult, FrozenHypothesis, PairExecutionResult, RunEvent, TestArtifact as DomainTestArtifact


def artifact(run_id="run-1", code="def test_ok():\n    assert True\n"):
    return DomainTestArtifact.create(run_id, "test-1", "h1", Arm.DIRECT, code, "prompt", ())


def request(repo: Path, test_artifact: DomainTestArtifact, timeout=5):
    return ExecutionRequest("run-1", "req-1", "fixture", repo, test_artifact, (sys.executable, "-m", "pytest", "-q"), {"PYTHONPATH": str(repo)}, timeout, "pytest")


def test_subprocess_executor_handles_pass_failure_and_cleanup(tmp_path):
    passing = artifact(code="def test_ok():\n    assert True\n")
    result = SubprocessExecutor().execute(request(tmp_path, passing))
    assert result.state is ExecutionState.PASS
    assert not list(tmp_path.glob("_generated_eval_*.py"))

    failing = artifact(code="def test_bad():\n    observed = 1\n    assert observed == 2\n")
    result = SubprocessExecutor().execute(request(tmp_path, failing))
    assert result.state is ExecutionState.FAIL
    assert result.failure_type is FailureType.ASSERTION_FAILURE
    assert "AssertionError" in result.normalized_log


def test_subprocess_executor_classifies_mechanical_import_failure(tmp_path):
    broken = artifact(code="from missing_module import nope\n\ndef test_bad():\n    assert True\n")
    result = SubprocessExecutor().execute(request(tmp_path, broken))
    assert result.state is ExecutionState.MECHANICAL_FAILURE
    assert result.failure_type is FailureType.MECHANICAL_FAILURE


def test_subprocess_executor_times_out_and_cleans_up(tmp_path):
    timed = artifact(code="import time\ndef test_slow():\n    time.sleep(2)\n")
    result = SubprocessExecutor().execute(request(tmp_path, timed, timeout=0.1))
    assert result.state is ExecutionState.TIMEOUT
    assert result.exit_code == 124
    assert "TIMEOUT" in result.normalized_log
    assert not list(tmp_path.glob("_generated_eval_*.py"))


def test_benchmark_evaluator_preserves_f2p_and_f2f_semantics():
    hypothesis = FrozenHypothesis.from_record("run-1", "h1", {"hypothesis": "encoding", "oracle": {"expected_behavior": "output preserves value", "target_evidence": "public output uses implicit encoding"}}, ())
    test = artifact()
    buggy = ExecutionResult("run-1", "buggy", "fixture", ExecutionState.FAIL, FailureType.ASSERTION_FAILURE, 1, "", "AssertionError", "AssertionError", "AssertionError")
    fixed = ExecutionResult("run-1", "fixed", "fixture", ExecutionState.PASS, FailureType.NONE, 0, "", "", "", "")
    pair = PairExecutionResult("run-1", "pair-1", test.stable_id, buggy, fixed, True)
    evaluated = BenchmarkEvaluator().evaluate(hypothesis, pair)
    assert evaluated.classification is PairClassification.F2P
    assert evaluated.verified_f2p is True

    same_failure = ExecutionResult("run-1", "fixed", "fixture", ExecutionState.FAIL, FailureType.ASSERTION_FAILURE, 1, "", "AssertionError", "AssertionError", "AssertionError")
    result = BenchmarkEvaluator().evaluate(hypothesis, PairExecutionResult("run-1", "pair-2", test.stable_id, buggy, same_failure, True))
    assert result.classification is PairClassification.F2F


def test_benchmark_evaluator_rejects_unsupported_oracle():
    hypothesis = FrozenHypothesis.from_record("run-1", "h1", {"hypothesis": "claim", "oracle": {}}, ())
    test = artifact()
    result = ExecutionResult("run-1", "x", "fixture", ExecutionState.PASS, FailureType.NONE, 0, "", "", "", "")
    evaluated = BenchmarkEvaluator().evaluate(hypothesis, PairExecutionResult("run-1", "pair", test.stable_id, result, result, True))
    assert evaluated.classification is PairClassification.UNSUPPORTED_ORACLE


def test_benchmark_evaluator_handles_exception_f2p_p2p_p2f_and_unchanged_test():
    hypothesis = FrozenHypothesis.from_record("run-1", "h1", {"hypothesis": "encoding", "oracle": {"expected_behavior": "output preserves value", "target_evidence": "target output encoding"}}, ())
    test = artifact()
    buggy_exception = ExecutionResult("run-1", "buggy", "fixture", ExecutionState.FAIL, FailureType.TARGET_EXCEPTION, 1, "", "pysnooper/tracer.py UnicodeEncodeError", "pysnooper/tracer.py UnicodeEncodeError", "UnicodeEncodeError")
    fixed_pass = ExecutionResult("run-1", "fixed", "fixture", ExecutionState.PASS, FailureType.NONE, 0, "", "", "", "")
    assert BenchmarkEvaluator(("pysnooper/",)).evaluate(hypothesis, PairExecutionResult("run-1", "pair-ex", test.stable_id, buggy_exception, fixed_pass, True)).classification is PairClassification.F2P
    assert BenchmarkEvaluator().evaluate(hypothesis, PairExecutionResult("run-1", "pair-p2p", test.stable_id, fixed_pass, fixed_pass, True)).classification is PairClassification.P2P
    fixed_failure = ExecutionResult("run-1", "fixed", "fixture", ExecutionState.FAIL, FailureType.ASSERTION_FAILURE, 1, "", "AssertionError", "AssertionError", "AssertionError")
    assert BenchmarkEvaluator().evaluate(hypothesis, PairExecutionResult("run-1", "pair-p2f", test.stable_id, fixed_pass, fixed_failure, True)).classification is PairClassification.P2F
    unverified = BenchmarkEvaluator().evaluate(hypothesis, PairExecutionResult("run-1", "pair-unchanged", test.stable_id, buggy_exception, fixed_pass, False))
    assert unverified.verified_f2p is False


def test_json_artifact_store_is_append_only_and_ordered(tmp_path):
    store = JsonArtifactStore(tmp_path)
    first = RunEvent("run-1", "e1", Stage.LOAD_CONFIG, "COMPLETE", {"value": 1})
    second = RunEvent("run-1", "e2", Stage.EVALUATE, "COMPLETE", {"value": 2})
    store.append_event(first)
    store.append_event(second)
    assert [event.event_id for event in store.load_run("run-1")] == ["e1", "e2"]
    with pytest.raises(ValueError, match="duplicate"):
        store.append_event(first)
    store.mark_completed("run-1")
    with pytest.raises(ValueError, match="completed"):
        store.save_artifact(artifact())
