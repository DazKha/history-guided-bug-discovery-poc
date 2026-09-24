from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from ..adapters.bugsinpy import BugsInPyTargetAdapter
from ..config.models import RunConfig
from ..domain.enums import Arm, ExecutionState, FailureType, Stage
from ..domain.models import (
    ExecutionRequest,
    ExecutionResult,
    FrozenHypothesis,
    PairExecutionResult,
    RunEvent,
    RunSummary,
    TargetSpec,
    TestArtifact,
    TriggerPlan,
    stable_hash,
)
from ..ports.artifact_store import ArtifactStore
from ..ports.evaluator import Evaluator
from ..ports.executor import TestExecutor
from ..ports.llm import LLMProvider
from ..ports.target import TargetAdapter
from .hypothesis_service import HypothesisService
from .planning_service import PlanningService
from .test_generation_service import TestGenerationService


class DiscoveryPipeline:
    def __init__(self, config: RunConfig, provider: LLMProvider, executor: TestExecutor, evaluator: Evaluator, store: ArtifactStore, target_adapter: TargetAdapter | None = None):
        self.config = config
        self.provider = provider
        self.executor = executor
        self.evaluator = evaluator
        self.store = store
        self.target_adapter = target_adapter or BugsInPyTargetAdapter(config.paths.target_context, config.generation_visible_manifest, str(config.target.get("python", "python3")), str(config.target.get("runner", "pytest")))
        self.hypotheses = HypothesisService()

    def run(self, arm: Arm, resume: bool = False) -> RunSummary:
        existing = self.store.load_run(self.config.run_id)
        if any(event.stage is Stage.REPORT and event.status == "COMPLETE" for event in existing):
            raise ValueError(f"run {self.config.run_id} is already complete; choose a new run_id")
        records = self.store.load_artifact_records(self.config.run_id)
        self._validate_immutable_records(records)
        self._event_once(Stage.LOAD_CONFIG, "COMPLETE", {"config_hash": self.config.config_hash})
        target = self._target_spec()
        prepared = self.target_adapter.prepare(target)
        context = self.target_adapter.build_context(prepared)
        self._event_once(Stage.PREPARE_TARGET, "COMPLETE", {"target_id": target.target_id, "context_hash": context.content_sha256})
        history = self.hypotheses.load_history(self.config)
        self._event_once(Stage.LOAD_HISTORY, "COMPLETE", {"records": len(history)})
        frozen = self.hypotheses.load_frozen(self.config)
        for hypothesis in frozen:
            self._save_immutable(hypothesis, records)
        self._event_once(Stage.LOAD_OR_GENERATE_HYPOTHESIS, "COMPLETE", {"mode": "frozen", "count": len(frozen)})
        self._event_once(Stage.FREEZE_HYPOTHESIS, "COMPLETE", {"hypotheses": len(frozen), "hashes": [item.hypothesis_sha256 for item in frozen]})
        generation = TestGenerationService(self.provider, self.config)
        planner = PlanningService(self.provider, self.config)
        for hypothesis in frozen:
            if arm is Arm.STRICT_PLANNER:
                candidates = self._planner_candidates(hypothesis, context.content, history, planner, records)
            else:
                count = self.config.planner.candidate_count if arm is Arm.BUDGET_MATCHED_DIRECT else 1
                candidates = [(f"direct-{index}", None) for index in range(1, count + 1)]
            for candidate_id, plan in candidates:
                self._run_candidate(hypothesis, arm, candidate_id, plan, context.content, target, generation, records)
        summary = self._reconstruct_summary(frozen)
        if self._all_candidates_complete(frozen, arm, records):
            self._save_immutable(summary, records)
            self._event_once(Stage.REPORT, "COMPLETE", summary.to_dict())
        return summary

    def _planner_candidates(self, hypothesis, target_context, history, service, records):
        persisted = [TriggerPlan.from_dict(record) for record in records if record.get("hypothesis_id") == hypothesis.hypothesis_id and "plan_id" in record]
        if persisted:
            return [(plan.plan_id, plan) for plan in sorted(persisted, key=lambda item: item.plan_id)]
        planning = service.generate(hypothesis, target_context, history)
        usage = {
            "llm_calls": len(planning.responses),
            "prompt_tokens": sum(int(response.usage.get("prompt_tokens", 0) or 0) for response in planning.responses),
            "completion_tokens": sum(int(response.usage.get("completion_tokens", 0) or 0) for response in planning.responses),
        }
        for plan in planning.plans:
            self._save_immutable(plan, records)
            self._event(Stage.VALIDATE_TRIGGER_PLAN, "COMPLETE", {"hypothesis_id": hypothesis.hypothesis_id, "plan_id": plan.plan_id, "plan_sha256": plan.plan_sha256})
        self._event(Stage.GENERATE_TRIGGER_PLAN, "COMPLETE" if planning.plans else "FAILED", {"hypothesis_id": hypothesis.hypothesis_id, "attempts": list(planning.attempts), "plans": [plan.to_dict() for plan in planning.plans], **usage})
        return [(plan.plan_id, plan) for plan in planning.plans]

    def _run_candidate(self, hypothesis, arm, candidate_id, plan, context, target, generation, records):
        artifact_id = f"{hypothesis.hypothesis_id}-{candidate_id}"
        events = self.store.load_run(self.config.run_id)
        generation_event = self._candidate_event(events, Stage.GENERATE_TEST, hypothesis.hypothesis_id, candidate_id)
        artifact = self._find_test_artifact(records, artifact_id)
        if generation_event is None and artifact is not None:
            usage = dict(artifact.usage)
            self._event(Stage.GENERATE_TEST, "TEST", {"hypothesis_id": hypothesis.hypothesis_id, "candidate_id": candidate_id, "artifact_id": artifact_id, "prompt_hash": artifact.prompt_hash, "model": artifact.model_name, "usage": usage, "llm_calls": 1, "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0), "completion_tokens": int(usage.get("completion_tokens", 0) or 0), "error": "reconstructed from persisted artifact"})
        elif generation_event is None:
            result = generation.generate(hypothesis, arm, artifact_id, plan, target_context=context)
            usage = dict(result.response.usage) if result.response is not None else {}
            if result.artifact is not None:
                artifact = result.artifact
                self._save_immutable(artifact, records)
            self._event(Stage.GENERATE_TEST, result.status, {"hypothesis_id": hypothesis.hypothesis_id, "candidate_id": candidate_id, "artifact_id": artifact_id, "prompt_hash": result.prompt_hash, "model": result.response.log_record.get("model") if result.response else "", "usage": usage, "llm_calls": 1 if result.response is not None else 0, "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0), "completion_tokens": int(usage.get("completion_tokens", 0) or 0), "error": result.error})
            if result.artifact is None:
                return
        elif artifact is None and generation_event.status != "MODEL_OUTPUT_FAILURE":
            raise ValueError(f"completed generation has no persisted artifact: {artifact_id}")
        if artifact is None:
            return
        events = self.store.load_run(self.config.run_id)
        if self._candidate_event(events, Stage.PREFLIGHT_TEST, hypothesis.hypothesis_id, candidate_id) is None:
            self._event(Stage.PREFLIGHT_TEST, "COMPLETE", {"hypothesis_id": hypothesis.hypothesis_id, "candidate_id": candidate_id, "artifact_id": artifact.stable_id, "test_sha256": artifact.test_sha256})
        if target.fixed_checkout is None:
            return
        events = self.store.load_run(self.config.run_id)
        buggy = self._execution_from_event(self._candidate_event(events, Stage.EXECUTE_BUGGY, hypothesis.hypothesis_id, candidate_id))
        if buggy is None:
            buggy = self.executor.execute(self._execution_request(target, artifact, "buggy"))
            self._event(Stage.EXECUTE_BUGGY, buggy.state.value, {"hypothesis_id": hypothesis.hypothesis_id, "candidate_id": candidate_id, **buggy.to_dict()})
        events = self.store.load_run(self.config.run_id)
        fixed = self._execution_from_event(self._candidate_event(events, Stage.EXECUTE_FIXED, hypothesis.hypothesis_id, candidate_id))
        if fixed is None:
            fixed = self.executor.execute(self._execution_request(target, artifact, "fixed"))
            self._event(Stage.EXECUTE_FIXED, fixed.state.value, {"hypothesis_id": hypothesis.hypothesis_id, "candidate_id": candidate_id, **fixed.to_dict()})
        events = self.store.load_run(self.config.run_id)
        if self._candidate_event(events, Stage.EVALUATE, hypothesis.hypothesis_id, candidate_id) is None:
            evaluation = self.evaluator.evaluate(hypothesis, PairExecutionResult(self.config.run_id, f"pair-{artifact.artifact_id}", artifact.stable_id, buggy, fixed, True))
            self._save_immutable(evaluation, records)
            self._event(Stage.EVALUATE, evaluation.classification.value, {"hypothesis_id": hypothesis.hypothesis_id, "candidate_id": candidate_id, **evaluation.to_dict()})
        if self._candidate_event(self.store.load_run(self.config.run_id), Stage.PERSIST, hypothesis.hypothesis_id, candidate_id) is None:
            self._event(Stage.PERSIST, "COMPLETE", {"hypothesis_id": hypothesis.hypothesis_id, "candidate_id": candidate_id, "artifact_id": artifact.stable_id})

    def _find_test_artifact(self, records, artifact_id):
        for record in records:
            if record.get("artifact_id") == artifact_id and "test_sha256" in record:
                if stable_hash(record.get("code", "")) != record.get("test_sha256"):
                    raise ValueError(f"test artifact hash mismatch: {artifact_id}")
                return TestArtifact.from_dict(record)
        return None

    def _validate_immutable_records(self, records):
        for record in records:
            if "code" in record and "test_sha256" in record and stable_hash(record["code"]) != record["test_sha256"]:
                raise ValueError(f"test artifact hash mismatch: {record.get('artifact_id', record.get('stable_id', 'unknown'))}")

    def _save_immutable(self, artifact, records):
        stable_id = artifact.stable_id
        current = artifact.to_dict()
        existing = next((record for record in records if record.get("stable_id") == stable_id), None)
        if existing is not None:
            if existing == current or (existing.get("hypothesis_sha256") and existing.get("hypothesis_sha256") == current.get("hypothesis_sha256")):
                return
            raise ValueError(f"immutable artifact disagreement: {stable_id}")
        self.store.save_artifact(artifact)
        records.append(current)

    def _candidate_event(self, events, stage, hypothesis_id, candidate_id):
        return next((event for event in events if event.stage is stage and event.payload.get("hypothesis_id") == hypothesis_id and event.payload.get("candidate_id") == candidate_id), None)

    def _execution_from_event(self, event):
        if event is None:
            return None
        value = event.payload
        return ExecutionResult(value["run_id"], value["request_id"], value["target_id"], ExecutionState(value["state"]), FailureType(value["failure_type"]), int(value["exit_code"]), value.get("stdout", ""), value.get("stderr", ""), value.get("normalized_log", ""), value.get("exception", ""), tuple(value.get("command", ())), float(value.get("duration_seconds", 0.0)), value.get("schema_version", "1"))

    def _all_candidates_complete(self, hypotheses, arm, records):
        for hypothesis in hypotheses:
            if arm is Arm.STRICT_PLANNER:
                candidate_ids = [record["plan_id"] for record in records if record.get("hypothesis_id") == hypothesis.hypothesis_id and "plan_id" in record]
                if not candidate_ids:
                    return False
            else:
                count = self.config.planner.candidate_count if arm is Arm.BUDGET_MATCHED_DIRECT else 1
                candidate_ids = [f"direct-{index}" for index in range(1, count + 1)]
            events = self.store.load_run(self.config.run_id)
            for candidate_id in candidate_ids:
                generation = self._candidate_event(events, Stage.GENERATE_TEST, hypothesis.hypothesis_id, candidate_id)
                if generation is None:
                    return False
                if generation.status == "MODEL_OUTPUT_FAILURE":
                    continue
                required = [Stage.PREFLIGHT_TEST, Stage.EXECUTE_BUGGY, Stage.EXECUTE_FIXED, Stage.EVALUATE, Stage.PERSIST]
                if any(self._candidate_event(events, stage, hypothesis.hypothesis_id, candidate_id) is None for stage in required):
                    return False
        return True

    def _reconstruct_summary(self, frozen):
        events = self.store.load_run(self.config.run_id)
        relevant = {Stage.GENERATE_TEST, Stage.GENERATE_TRIGGER_PLAN}
        prompt_hashes = tuple(event.payload.get("prompt_hash") for event in events if event.stage is Stage.GENERATE_TEST and event.payload.get("prompt_hash"))
        calls = sum(int(event.payload.get("llm_calls", 0) or 0) for event in events if event.stage in relevant)
        prompt_tokens = sum(int(event.payload.get("prompt_tokens", 0) or 0) for event in events if event.stage in relevant)
        completion_tokens = sum(int(event.payload.get("completion_tokens", 0) or 0) for event in events if event.stage in relevant)
        return RunSummary(self.config.run_id, self.config.config_hash, self.config.source_commit or _source_commit(), {"hypotheses": len(frozen), "prompt_calls": calls, "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens}, prompt_hashes, getattr(self.evaluator, "version", ""))

    def _event_once(self, stage, status, payload):
        if not any(event.stage is stage and event.status == status for event in self.store.load_run(self.config.run_id)):
            self._event(stage, status, payload)

    def _target_spec(self) -> TargetSpec:
        target = self.config.target
        buggy = Path(str(target.get("buggy_checkout", ""))).resolve()
        fixed_value = target.get("fixed_checkout")
        fixed = Path(str(fixed_value)).resolve() if fixed_value else None
        return TargetSpec(self.config.run_id, self.config.target_id, buggy, fixed, str(target.get("python", "python3")), str(target.get("runner", "pytest")), self.config.execution.environment, tuple(target.get("source_path_markers", ())))

    def _execution_request(self, target: TargetSpec, artifact, revision: str) -> ExecutionRequest:
        checkout = target.buggy_checkout if revision == "buggy" else target.fixed_checkout
        assert checkout is not None
        runner = self.target_adapter.select_runner(artifact)
        executable = runner.executable
        configured = Path(target.python_executable)
        if not configured.is_absolute():
            candidate = checkout / configured
            if candidate.exists():
                executable = str(candidate)
        return ExecutionRequest(self.config.run_id, f"{artifact.artifact_id}-{revision}", target.target_id, checkout, artifact, (executable, *runner.arguments), self.config.execution.environment, self.config.execution.timeout_seconds, target.runner)

    def _event(self, stage: Stage, status: str, payload: dict[str, Any]) -> None:
        event_id = f"{stage.value.lower()}-{len(self.store.load_run(self.config.run_id)) + 1}"
        self.store.append_event(RunEvent(self.config.run_id, event_id, stage, status, payload))


def _source_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"
