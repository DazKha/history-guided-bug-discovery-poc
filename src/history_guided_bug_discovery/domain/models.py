from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from pathlib import Path
from typing import Any, Mapping

from .enums import (
    Arm, ArtifactStatus, ExecutionState, FailureCategory, FailureType,
    PairClassification, Stage,
)

SCHEMA_VERSION = "1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(v) for v in value]
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return value


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def canonical_json(value: Any) -> str:
    # Keep the historical hypothesis digest compatible with the Experiment 3/4
    # freeze function while still fixing key ordering and Unicode handling.
    return json.dumps(_jsonable(value), sort_keys=True, ensure_ascii=False)


def stable_hash(value: Any) -> str:
    if isinstance(value, str):
        raw = value.encode("utf-8")
    else:
        raw = value if isinstance(value, (bytes, bytearray)) else canonical_json(value).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class TargetSpec:
    run_id: str
    target_id: str
    buggy_checkout: Path
    fixed_checkout: Path | None
    python_executable: str
    runner: str
    environment: Mapping[str, str] = field(default_factory=dict)
    source_path_markers: tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION

    @property
    def stable_id(self) -> str:
        return f"{self.run_id}:{self.target_id}"

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "stable_id": self.stable_id, "run_id": self.run_id, "target_id": self.target_id, "buggy_checkout": str(self.buggy_checkout), "fixed_checkout": str(self.fixed_checkout) if self.fixed_checkout else None, "python_executable": self.python_executable, "runner": self.runner, "environment": dict(sorted(self.environment.items())), "source_path_markers": list(self.source_path_markers)}


@dataclass(frozen=True)
class TargetContext:
    run_id: str
    target_id: str
    content: str
    visible_files: tuple[str, ...]
    content_sha256: str
    schema_version: str = SCHEMA_VERSION

    @classmethod
    def create(cls, run_id: str, target_id: str, content: str, visible_files: tuple[str, ...]) -> "TargetContext":
        return cls(run_id, target_id, content, tuple(visible_files), stable_hash(content), SCHEMA_VERSION)

    @property
    def stable_id(self) -> str:
        return f"{self.run_id}:{self.target_id}:context"

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "stable_id": self.stable_id, "run_id": self.run_id, "target_id": self.target_id, "content": self.content, "visible_files": list(self.visible_files), "content_sha256": self.content_sha256}


@dataclass(frozen=True)
class HistoricalBugUnit:
    run_id: str
    history_id: str
    summary: str
    mechanism: str
    provenance: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    @property
    def stable_id(self) -> str:
        return f"{self.run_id}:{self.history_id}"

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "stable_id": self.stable_id, "run_id": self.run_id, "history_id": self.history_id, "summary": self.summary, "mechanism": self.mechanism, "provenance": _jsonable(self.provenance)}


@dataclass(frozen=True)
class FrozenHypothesis:
    run_id: str
    hypothesis_id: str
    claim: str
    trigger: str
    potential_failure: str
    oracle: Mapping[str, Any]
    hypothesis_sha256: str
    generation_visible_files: tuple[str, ...]
    created_at: str = field(default_factory=_now)
    schema_version: str = SCHEMA_VERSION

    @classmethod
    def from_record(cls, run_id: str, hypothesis_id: str, record: Mapping[str, Any], generation_visible_files: tuple[str, ...]) -> "FrozenHypothesis":
        claim = str(record.get("hypothesis", record.get("claim", "")))
        trigger = str(record.get("trigger", ""))
        potential_failure = str(record.get("potential_failure", ""))
        oracle = dict(record.get("oracle", {}) or {})
        digest_input = {"hypothesis": claim, "trigger": trigger, "potential_failure": potential_failure, "oracle": oracle}
        return cls(run_id, hypothesis_id, claim, trigger, potential_failure, _freeze(oracle), stable_hash(digest_input), tuple(generation_visible_files))

    @property
    def stable_id(self) -> str:
        return f"{self.run_id}:{self.hypothesis_id}"

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "stable_id": self.stable_id, "run_id": self.run_id, "hypothesis_id": self.hypothesis_id, "claim": self.claim, "trigger": self.trigger, "potential_failure": self.potential_failure, "oracle": _jsonable(self.oracle), "hypothesis_sha256": self.hypothesis_sha256, "hypothesis_frozen": True, "generation_visible_files": list(self.generation_visible_files), "created_at": self.created_at}


@dataclass(frozen=True)
class TriggerPlan:
    run_id: str
    hypothesis_id: str
    plan_id: str
    plan: Mapping[str, Any]
    prompt_hash: str
    plan_sha256: str
    strategy: str = "strict_trigger_plan_v1"
    created_at: str = field(default_factory=_now)
    schema_version: str = SCHEMA_VERSION

    @property
    def stable_id(self) -> str:
        return f"{self.run_id}:{self.hypothesis_id}:{self.plan_id}"

    @classmethod
    def create(cls, run_id: str, hypothesis_id: str, plan_id: str, plan: Mapping[str, Any], prompt_hash: str, strategy: str = "strict_trigger_plan_v1") -> "TriggerPlan":
        return cls(run_id, hypothesis_id, plan_id, dict(plan), prompt_hash, stable_hash(plan), strategy)

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "stable_id": self.stable_id, "run_id": self.run_id, "hypothesis_id": self.hypothesis_id, "plan_id": self.plan_id, "plan": _jsonable(self.plan), "prompt_hash": self.prompt_hash, "plan_sha256": self.plan_sha256, "strategy": self.strategy, "created_at": self.created_at}


@dataclass(frozen=True)
class TestArtifact:
    run_id: str
    artifact_id: str
    hypothesis_id: str
    arm: Arm
    code: str
    test_sha256: str
    prompt_hash: str
    generation_visible_manifest: tuple[str, ...]
    status: ArtifactStatus = ArtifactStatus.GENERATED
    plan_id: str | None = None
    prompt_strategy: str = ""
    model_name: str = ""
    usage: Mapping[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now)
    schema_version: str = SCHEMA_VERSION

    @classmethod
    def create(cls, run_id: str, artifact_id: str, hypothesis_id: str, arm: Arm, code: str, prompt_hash: str, generation_visible_manifest: tuple[str, ...], plan_id: str | None = None, prompt_strategy: str = "", model_name: str = "", usage: Mapping[str, Any] | None = None) -> "TestArtifact":
        return cls(run_id, artifact_id, hypothesis_id, arm, code, stable_hash(code), prompt_hash, tuple(generation_visible_manifest), ArtifactStatus.GENERATED, plan_id, prompt_strategy, model_name, dict(usage or {}))

    @property
    def stable_id(self) -> str:
        return f"{self.run_id}:{self.artifact_id}"

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "stable_id": self.stable_id, "run_id": self.run_id, "artifact_id": self.artifact_id, "hypothesis_id": self.hypothesis_id, "arm": self.arm.value, "code": self.code, "test_sha256": self.test_sha256, "prompt_hash": self.prompt_hash, "prompt_strategy": self.prompt_strategy, "model_name": self.model_name, "usage": _jsonable(self.usage), "generation_visible_manifest": list(self.generation_visible_manifest), "status": self.status.value, "plan_id": self.plan_id, "created_at": self.created_at}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "TestArtifact":
        return cls(value["run_id"], value["artifact_id"], value["hypothesis_id"], Arm(value["arm"]), value["code"], value["test_sha256"], value["prompt_hash"], tuple(value.get("generation_visible_manifest", ())), ArtifactStatus(value.get("status", ArtifactStatus.GENERATED.value)), value.get("plan_id"), value.get("prompt_strategy", ""), value.get("model_name", ""), value.get("usage", {}), value.get("created_at", ""), value.get("schema_version", SCHEMA_VERSION))


@dataclass(frozen=True)
class ExecutionRequest:
    run_id: str
    request_id: str
    target_id: str
    target_checkout: Path
    test_artifact: TestArtifact
    command: tuple[str, ...]
    environment: Mapping[str, str]
    timeout_seconds: float
    runner: str
    schema_version: str = SCHEMA_VERSION

    @property
    def stable_id(self) -> str:
        return f"{self.run_id}:{self.request_id}"

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "stable_id": self.stable_id, "run_id": self.run_id, "request_id": self.request_id, "target_id": self.target_id, "target_checkout": str(self.target_checkout), "test_artifact": self.test_artifact.to_dict(), "command": list(self.command), "environment": dict(sorted(self.environment.items())), "timeout_seconds": self.timeout_seconds, "runner": self.runner}


@dataclass(frozen=True)
class ExecutionResult:
    run_id: str
    request_id: str
    target_id: str
    state: ExecutionState
    failure_type: FailureType
    exit_code: int
    stdout: str
    stderr: str
    normalized_log: str
    exception: str = ""
    command: tuple[str, ...] = ()
    duration_seconds: float = 0.0
    schema_version: str = SCHEMA_VERSION

    @property
    def stable_id(self) -> str:
        return f"{self.run_id}:{self.request_id}:result"

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "stable_id": self.stable_id, "run_id": self.run_id, "request_id": self.request_id, "target_id": self.target_id, "state": self.state.value, "failure_type": self.failure_type.value, "exit_code": self.exit_code, "stdout": self.stdout, "stderr": self.stderr, "normalized_log": self.normalized_log, "exception": self.exception, "command": list(self.command), "duration_seconds": self.duration_seconds}


@dataclass(frozen=True)
class PairExecutionResult:
    run_id: str
    pair_id: str
    test_artifact_id: str
    buggy: ExecutionResult
    fixed: ExecutionResult
    same_test: bool
    schema_version: str = SCHEMA_VERSION

    @property
    def stable_id(self) -> str:
        return f"{self.run_id}:{self.pair_id}"

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "stable_id": self.stable_id, "run_id": self.run_id, "pair_id": self.pair_id, "test_artifact_id": self.test_artifact_id, "buggy": self.buggy.to_dict(), "fixed": self.fixed.to_dict(), "same_test": self.same_test}


@dataclass(frozen=True)
class EvaluationResult:
    run_id: str
    evaluation_id: str
    hypothesis_id: str
    test_artifact_id: str
    classification: PairClassification
    failure_category: FailureCategory
    verified_f2p: bool
    oracle_supported: bool
    activation: str
    evaluator_version: str
    provenance: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    @property
    def stable_id(self) -> str:
        return f"{self.run_id}:{self.evaluation_id}"

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "stable_id": self.stable_id, "run_id": self.run_id, "evaluation_id": self.evaluation_id, "hypothesis_id": self.hypothesis_id, "test_artifact_id": self.test_artifact_id, "classification": self.classification.value, "failure_category": self.failure_category.value, "verified_f2p": self.verified_f2p, "oracle_supported": self.oracle_supported, "activation": self.activation, "evaluator_version": self.evaluator_version, "provenance": _jsonable(self.provenance)}


@dataclass(frozen=True)
class RunEvent:
    run_id: str
    event_id: str
    stage: Stage
    status: str
    payload: Mapping[str, Any]
    created_at: str = field(default_factory=_now)
    schema_version: str = SCHEMA_VERSION

    @property
    def stable_id(self) -> str:
        return f"{self.run_id}:{self.event_id}"

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "stable_id": self.stable_id, "run_id": self.run_id, "event_id": self.event_id, "stage": self.stage.value, "status": self.status, "payload": _jsonable(self.payload), "created_at": self.created_at}


@dataclass(frozen=True)
class RunSummary:
    run_id: str
    config_hash: str
    source_commit: str
    metrics: Mapping[str, Any]
    prompt_hashes: tuple[str, ...] = ()
    evaluator_version: str = ""
    created_at: str = field(default_factory=_now)
    schema_version: str = SCHEMA_VERSION

    @property
    def stable_id(self) -> str:
        return self.run_id

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "stable_id": self.stable_id, "run_id": self.run_id, "config_hash": self.config_hash, "source_commit": self.source_commit, "metrics": _jsonable(self.metrics), "prompt_hashes": list(self.prompt_hashes), "evaluator_version": self.evaluator_version, "created_at": self.created_at}
