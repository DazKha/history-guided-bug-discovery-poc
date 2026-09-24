from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from ..adapters.bugsinpy import BugsInPyTargetAdapter
from ..config.models import RunConfig
from ..domain.enums import Arm, Stage
from ..domain.models import ExecutionRequest, FrozenHypothesis, PairExecutionResult, RunEvent, RunSummary, TargetSpec
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
        self._event(Stage.LOAD_CONFIG, "COMPLETE", {"config_hash": self.config.config_hash})
        target = self._target_spec()
        prepared = self.target_adapter.prepare(target)
        context = self.target_adapter.build_context(prepared)
        self._event(Stage.PREPARE_TARGET, "COMPLETE", {"target_id": target.target_id, "context_hash": context.content_sha256})
        history = self.hypotheses.load_history(self.config)
        self._event(Stage.LOAD_HISTORY, "COMPLETE", {"records": len(history)})
        frozen = self.hypotheses.load_frozen(self.config)
        for hypothesis in frozen:
            self.store.save_artifact(hypothesis)
        self._event(Stage.LOAD_OR_GENERATE_HYPOTHESIS, "COMPLETE", {"mode": "frozen", "count": len(frozen)})
        self._event(Stage.FREEZE_HYPOTHESIS, "COMPLETE", {"hypotheses": len(frozen), "hashes": [item.hypothesis_sha256 for item in frozen]})
        generation = TestGenerationService(self.provider, self.config)
        plans = PlanningService(self.provider, self.config)
        prompt_hashes: list[str] = []
        llm_calls = prompt_tokens = completion_tokens = 0
        for hypothesis in frozen:
            if arm is Arm.STRICT_PLANNER:
                planning = plans.generate(hypothesis, context.content, history)
                llm_calls += len(planning.responses)
                prompt_tokens += sum(int(response.usage.get("prompt_tokens", 0) or 0) for response in planning.responses)
                completion_tokens += sum(int(response.usage.get("completion_tokens", 0) or 0) for response in planning.responses)
                for plan in planning.plans:
                    self.store.save_artifact(plan)
                    self._event(Stage.VALIDATE_TRIGGER_PLAN, "COMPLETE", {"plan_id": plan.plan_id, "plan_sha256": plan.plan_sha256})
                self._event(Stage.GENERATE_TRIGGER_PLAN, "COMPLETE" if planning.plans else "FAILED", {"hypothesis_id": hypothesis.hypothesis_id, "attempts": list(planning.attempts), "plans": [plan.to_dict() for plan in planning.plans]})
                candidates = [(plan.plan_id, plan) for plan in planning.plans]
            else:
                candidates = [(f"direct-{index}", None) for index in range(1, self.config.planner.candidate_count + 1 if arm is Arm.BUDGET_MATCHED_DIRECT else 2)]
            for candidate_id, plan in candidates:
                if resume and any(event.stage is Stage.GENERATE_TEST and event.payload.get("candidate_id") == candidate_id and event.payload.get("hypothesis_id") == hypothesis.hypothesis_id for event in existing):
                    continue
                result = generation.generate(hypothesis, arm, f"{hypothesis.hypothesis_id}-{candidate_id}", plan, context.content)
                prompt_hashes.append(result.prompt_hash)
                if result.response is not None:
                    llm_calls += 1
                    prompt_tokens += int(result.response.usage.get("prompt_tokens", 0) or 0)
                    completion_tokens += int(result.response.usage.get("completion_tokens", 0) or 0)
                self._event(Stage.GENERATE_TEST, result.status, {"hypothesis_id": hypothesis.hypothesis_id, "candidate_id": candidate_id, "prompt_hash": result.prompt_hash, "model": result.response.log_record.get("model") if result.response else "", "usage": dict(result.response.usage) if result.response else {}, "error": result.error})
                if result.artifact is None:
                    continue
                self.store.save_artifact(result.artifact)
                self._event(Stage.PREFLIGHT_TEST, "COMPLETE", {"artifact_id": result.artifact.stable_id, "test_sha256": result.artifact.test_sha256})
                if target.fixed_checkout is None:
                    continue
                buggy_request = self._execution_request(target, result.artifact, "buggy")
                fixed_request = self._execution_request(target, result.artifact, "fixed")
                buggy = self.executor.execute(buggy_request)
                self._event(Stage.EXECUTE_BUGGY, buggy.state.value, buggy.to_dict())
                fixed = self.executor.execute(fixed_request)
                self._event(Stage.EXECUTE_FIXED, fixed.state.value, fixed.to_dict())
                evaluation = self.evaluator.evaluate(hypothesis, PairExecutionResult(self.config.run_id, f"pair-{result.artifact.artifact_id}", result.artifact.stable_id, buggy, fixed, True))
                self.store.save_artifact(evaluation)
                self._event(Stage.PERSIST, "COMPLETE", {"artifact_id": result.artifact.stable_id, "evaluation_id": evaluation.evaluation_id})
                self._event(Stage.EVALUATE, evaluation.classification.value, evaluation.to_dict())
        summary = RunSummary(self.config.run_id, self.config.config_hash, self.config.source_commit or _source_commit(), {"hypotheses": len(frozen), "prompt_calls": llm_calls, "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens}, tuple(prompt_hashes), getattr(self.evaluator, "version", ""))
        self.store.save_artifact(summary)
        self._event(Stage.REPORT, "COMPLETE", summary.to_dict())
        return summary

    def _target_spec(self) -> TargetSpec:
        target = self.config.target
        buggy = Path(str(target.get("buggy_checkout", ""))).resolve()
        fixed_value = target.get("fixed_checkout")
        fixed = Path(str(fixed_value)).resolve() if fixed_value else None
        executable = str(target.get("python", "python3"))
        if not Path(executable).is_absolute() and buggy.exists():
            candidate = buggy / executable
            executable = str(candidate if candidate.exists() else Path(executable))
        return TargetSpec(self.config.run_id, self.config.target_id, buggy, fixed, executable, str(target.get("runner", "pytest")), self.config.execution.environment, tuple(target.get("source_path_markers", ())))

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
