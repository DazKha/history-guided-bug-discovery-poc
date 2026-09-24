import json
from dataclasses import replace
from pathlib import Path

import pytest

from history_guided_bug_discovery.adapters.json_artifact_store import JsonArtifactStore
from history_guided_bug_discovery.application.discovery_pipeline import DiscoveryPipeline
from history_guided_bug_discovery.config.loader import load_config
from history_guided_bug_discovery.domain.enums import Arm, ExecutionState, FailureType, Stage
from history_guided_bug_discovery.domain.models import ExecutionResult, RunEvent, TargetContext, TriggerPlan
from history_guided_bug_discovery.config.models import BudgetConfig
from history_guided_bug_discovery.ports.llm import GenerationResponse


ROOT = Path(__file__).resolve().parents[2]


class FakeProvider:
    def __init__(self):
        self.calls = 0

    def generate(self, request):
        self.calls += 1
        return GenerationResponse(
            json.dumps({"status": "TEST", "test_code": "def test_generated():\n    assert True\n"}),
            {"prompt_tokens": 1, "completion_tokens": 1}, self.calls, {"model": request.model},
        )


class FakeTargetAdapter:
    def prepare(self, target):
        from history_guided_bug_discovery.ports.target import PreparedTarget
        return PreparedTarget(target, target.buggy_checkout)

    def build_context(self, target):
        return TargetContext.create(target.spec.run_id, target.spec.target_id, "public target context", ("context.txt",))

    def select_runner(self, test):
        from history_guided_bug_discovery.ports.target import TestRunner
        return TestRunner("python", ("-m", "pytest", "-q"))


class FakeExecutor:
    def __init__(self):
        self.calls = []

    def execute(self, request):
        self.calls.append(request.request_id)
        return ExecutionResult(request.run_id, request.request_id, request.target_id, ExecutionState.PASS, FailureType.NONE, 0, "", "", "", "")


class CrashAfterStageStore(JsonArtifactStore):
    def __init__(self, root, stage):
        super().__init__(root)
        self.stage = stage
        self.crashed = False

    def append_event(self, event):
        super().append_event(event)
        if not self.crashed and event.stage is self.stage:
            self.crashed = True
            raise RuntimeError(f"simulated crash after {event.stage.value}")


class CrashBeforeStageEventStore(JsonArtifactStore):
    def __init__(self, root, stage):
        super().__init__(root)
        self.stage = stage
        self.crashed = False

    def append_event(self, event):
        if not self.crashed and event.stage is self.stage:
            self.crashed = True
            raise RuntimeError(f"simulated crash before {event.stage.value}")
        super().append_event(event)


def make_pipeline(tmp_path, store, provider, executor):
    config = load_config(ROOT / "configs/experiment4.json", ROOT)
    target = tmp_path / "target"
    target.mkdir(exist_ok=True)
    local_paths = replace(config.paths, artifact_root=tmp_path / "artifacts")
    local_config = replace(
        config,
        run_id="resume-test",
        paths=local_paths,
        target={"buggy_checkout": str(target), "fixed_checkout": str(target), "python": "python", "runner": "pytest", "source_path_markers": []},
    )
    from history_guided_bug_discovery.adapters.benchmark_evaluator import BenchmarkEvaluator
    return DiscoveryPipeline(local_config, provider, executor, BenchmarkEvaluator(()), store, FakeTargetAdapter())


@pytest.mark.parametrize("crash_stage", [Stage.GENERATE_TEST, Stage.EXECUTE_BUGGY, Stage.EXECUTE_FIXED, Stage.EVALUATE])
def test_resume_continues_first_incomplete_stage_without_duplicate_calls(tmp_path, crash_stage):
    store = CrashAfterStageStore(tmp_path / "artifacts", crash_stage)
    provider = FakeProvider()
    executor = FakeExecutor()
    pipeline = make_pipeline(tmp_path, store, provider, executor)

    with pytest.raises(RuntimeError, match="simulated crash"):
        pipeline.run(Arm.DIRECT)
    first_call_count = provider.calls
    with pytest.raises(ValueError, match="--resume|new run_id"):
        pipeline.run(Arm.DIRECT)
    summary = pipeline.run(Arm.DIRECT, resume=True)

    assert first_call_count == 1
    assert provider.calls == 5
    assert summary.metrics["hypotheses"] == 5
    events = store.load_run("resume-test")
    evaluations = [event for event in events if event.stage is Stage.EVALUATE]
    assert len(evaluations) == 5
    assert len({event.payload["evaluation_id"] for event in evaluations}) == 5
    assert sum(event.stage is Stage.REPORT for event in events) == 1
    with pytest.raises(ValueError, match="already complete"):
        pipeline.run(Arm.DIRECT, resume=True)


def test_resume_rejects_mutated_persisted_test_artifact(tmp_path):
    store = CrashAfterStageStore(tmp_path / "artifacts", Stage.GENERATE_TEST)
    provider = FakeProvider()
    pipeline = make_pipeline(tmp_path, store, provider, FakeExecutor())
    with pytest.raises(RuntimeError):
        pipeline.run(Arm.DIRECT)
    artifact_path = next(path for path in (tmp_path / "artifacts" / "resume-test" / "artifacts").glob("*.json") if "code" in json.loads(path.read_text(encoding="utf-8")))
    value = json.loads(artifact_path.read_text(encoding="utf-8"))
    value["code"] = "def test_mutated():\n    assert False\n"
    artifact_path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="hash"):
        pipeline.run(Arm.DIRECT, resume=True)


def test_resume_reconstructs_generation_from_durable_artifact_without_provider_call(tmp_path):
    store = CrashBeforeStageEventStore(tmp_path / "artifacts", Stage.GENERATE_TEST)
    provider = FakeProvider()
    pipeline = make_pipeline(tmp_path, store, provider, FakeExecutor())
    with pytest.raises(RuntimeError, match="before GENERATE_TEST"):
        pipeline.run(Arm.DIRECT)
    assert provider.calls == 1
    summary = pipeline.run(Arm.DIRECT, resume=True)
    assert provider.calls == 5
    assert summary.metrics["hypotheses"] == 5


def _seed_planner_terminal(pipeline, store, status="COMPLETE", partial=False):
    hypotheses = pipeline.hypotheses.load_frozen(pipeline.config)
    for hypothesis in hypotheses:
        plans = []
        if status == "COMPLETE" or partial:
            count = 1 if partial else pipeline.config.planner.candidate_count
            for index in range(1, count + 1):
                plan = TriggerPlan.create(
                    pipeline.config.run_id,
                    hypothesis.hypothesis_id,
                    f"plan-{index}",
                    {"index": index},
                    f"prompt-{hypothesis.hypothesis_id}",
                )
                store.save_artifact(plan)
                plans.append(plan)
        if status != "NONE":
            store.append_event(
                RunEvent(
                    pipeline.config.run_id,
                    f"planner-{hypothesis.hypothesis_id}",
                    Stage.GENERATE_TRIGGER_PLAN,
                    status,
                    {"hypothesis_id": hypothesis.hypothesis_id, "plans": [plan.to_dict() for plan in plans]},
                )
            )


def test_planner_failure_with_zero_plans_is_terminal(tmp_path):
    store = JsonArtifactStore(tmp_path / "artifacts")
    provider = FakeProvider()
    pipeline = make_pipeline(tmp_path, store, provider, FakeExecutor())
    summary = pipeline.run(Arm.STRICT_PLANNER)
    events = store.load_run("resume-test")
    assert summary.metrics["hypotheses"] == 5
    assert sum(event.stage is Stage.GENERATE_TRIGGER_PLAN and event.status == "FAILED" for event in events) == 5
    assert sum(event.stage is Stage.REPORT and event.status == "COMPLETE" for event in events) == 1


def test_partial_persisted_planner_state_is_rejected(tmp_path):
    store = JsonArtifactStore(tmp_path / "artifacts")
    pipeline = make_pipeline(tmp_path, store, FakeProvider(), FakeExecutor())
    first = pipeline.hypotheses.load_frozen(pipeline.config)[0]
    plan = TriggerPlan.create(pipeline.config.run_id, first.hypothesis_id, "plan-1", {"index": 1}, "prompt")
    store.save_artifact(plan)
    with pytest.raises(ValueError, match="incomplete|ambiguous"):
        pipeline.run(Arm.STRICT_PLANNER, resume=True)


def test_complete_persisted_planner_batch_is_not_regenerated(tmp_path):
    store = JsonArtifactStore(tmp_path / "artifacts")
    provider = FakeProvider()
    pipeline = make_pipeline(tmp_path, store, provider, FakeExecutor())
    pipeline.config = replace(pipeline.config, planner=BudgetConfig(pipeline.config.planner.strategy, 1, 0))
    _seed_planner_terminal(pipeline, store)
    summary = pipeline.run(Arm.STRICT_PLANNER, resume=True)
    assert summary.metrics["hypotheses"] == 5
    assert provider.calls == 5
