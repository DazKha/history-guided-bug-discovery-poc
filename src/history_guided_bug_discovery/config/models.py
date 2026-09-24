from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from ..domain.models import SCHEMA_VERSION, canonical_json, stable_hash


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    name: str
    temperature: float
    max_output_tokens: int
    thinking: str
    response_format: str = "json_object"
    timeout_seconds: float = 120.0

    def to_dict(self) -> dict[str, Any]:
        return {"provider": self.provider, "name": self.name, "temperature": self.temperature, "max_output_tokens": self.max_output_tokens, "thinking": self.thinking, "response_format": self.response_format, "timeout_seconds": self.timeout_seconds}


@dataclass(frozen=True)
class BudgetConfig:
    strategy: str
    candidate_count: int
    max_repairs: int

    def to_dict(self) -> dict[str, Any]:
        return {"strategy": self.strategy, "candidate_count": self.candidate_count, "max_repairs": self.max_repairs}


@dataclass(frozen=True)
class ExecutionConfig:
    timeout_seconds: float
    environment: Mapping[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {"timeout_seconds": self.timeout_seconds, "environment": dict(sorted(self.environment.items()))}


@dataclass(frozen=True)
class EvaluatorConfig:
    strategy: str
    version: str = "benchmark_f2p_v1"

    def to_dict(self) -> dict[str, Any]:
        return {"strategy": self.strategy, "version": self.version}


@dataclass(frozen=True)
class RunPaths:
    target_context: Path
    structured_history: Path
    frozen_hypotheses: Path
    artifact_root: Path
    target_manifest: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"target_context": str(self.target_context), "structured_history": str(self.structured_history), "frozen_hypotheses": str(self.frozen_hypotheses), "artifact_root": str(self.artifact_root), "target_manifest": str(self.target_manifest) if self.target_manifest else None}


@dataclass(frozen=True)
class RunConfig:
    schema_version: str
    run_id: str
    target_id: str
    target_context: str
    structured_history: str
    frozen_hypotheses: str
    model: ModelConfig
    planner: BudgetConfig
    execution: ExecutionConfig
    evaluator: EvaluatorConfig
    paths: RunPaths
    target: Mapping[str, Any]
    config_hash: str
    source_commit: str = ""
    repository_root: Path = Path(".")

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "run_id": self.run_id, "target_id": self.target_id, "target_context": self.target_context, "structured_history": self.structured_history, "frozen_hypotheses": self.frozen_hypotheses, "model": self.model.to_dict(), "planner": self.planner.to_dict(), "execution": self.execution.to_dict(), "evaluator": self.evaluator.to_dict(), "paths": self.paths.to_dict(), "target": dict(self.target), "config_hash": self.config_hash, "source_commit": self.source_commit, "repository_root": str(self.repository_root)}

    @property
    def generation_visible_manifest(self) -> tuple[str, ...]:
        return (self.target_context, self.structured_history)

    @property
    def deterministic_hash(self) -> str:
        return stable_hash({k: v for k, v in self.to_dict().items() if k not in {"config_hash", "source_commit"}})
