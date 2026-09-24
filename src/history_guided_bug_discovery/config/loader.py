from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..domain.errors import ConfigurationError
from ..domain.models import SCHEMA_VERSION, stable_hash
from .models import BudgetConfig, EvaluatorConfig, ExecutionConfig, ModelConfig, RunConfig, RunPaths

ConfigError = ConfigurationError


def _check_fields(value: dict[str, Any], allowed: set[str], scope: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ConfigError(f"unknown {scope} field(s): {', '.join(unknown)}")


def _path(value: str, config_path: Path, repository_root: Path) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    base = config_path.parent if config_path.parent != Path(".") else repository_root
    resolved = (base / candidate).resolve()
    if not resolved.exists():
        fallback = (repository_root / candidate).resolve()
        if fallback.exists():
            return fallback
    return resolved


def load_config(path: str | Path, repository_root: str | Path | None = None) -> RunConfig:
    config_path = Path(path).resolve()
    root = Path(repository_root or config_path.parents[1]).resolve()
    try:
        raw = json.loads(config_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"cannot load config {config_path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigError("config must be a JSON object")
    _check_fields(raw, {"schema_version", "run_id", "target_id", "target_context", "structured_history", "frozen_hypotheses", "model", "planner", "execution", "evaluator", "target", "artifact_root", "target_manifest"}, "config")
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise ConfigError(f"unsupported schema_version: {raw.get('schema_version')}")
    for field in ("run_id", "target_id", "target_context", "structured_history", "frozen_hypotheses"):
        if not isinstance(raw.get(field), str) or not raw[field].strip():
            raise ConfigError(f"{field} must be a non-empty string")

    model = raw.get("model")
    if not isinstance(model, dict):
        raise ConfigError("model must be an object")
    _check_fields(model, {"provider", "name", "temperature", "max_output_tokens", "thinking", "response_format", "timeout_seconds"}, "model")
    for field in ("provider", "name"):
        if not isinstance(model.get(field), str) or not model[field].strip():
            raise ConfigError(f"model.{field} must be a non-empty string")
    temperature = model.get("temperature")
    max_tokens = model.get("max_output_tokens")
    if isinstance(temperature, bool) or not isinstance(temperature, (int, float)) or not 0 <= temperature <= 2:
        raise ConfigError("temperature must be between 0 and 2")
    if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or max_tokens <= 0:
        raise ConfigError("max_output_tokens must be positive")
    model_config = ModelConfig(str(model["provider"]), str(model["name"]), float(temperature), max_tokens, str(model.get("thinking", "disabled")), str(model.get("response_format", "json_object")), float(model.get("timeout_seconds", 120)))

    planner = raw.get("planner")
    if not isinstance(planner, dict):
        raise ConfigError("planner must be an object")
    _check_fields(planner, {"strategy", "candidate_count", "max_repairs"}, "planner")
    if not isinstance(planner.get("strategy"), str) or not planner["strategy"].strip():
        raise ConfigError("planner.strategy must be a non-empty string")
    candidate_count, max_repairs = planner.get("candidate_count"), planner.get("max_repairs")
    if not isinstance(candidate_count, int) or candidate_count <= 0:
        raise ConfigError("candidate_count must be positive")
    if not isinstance(max_repairs, int) or max_repairs < 0:
        raise ConfigError("max_repairs must be non-negative")
    planner_config = BudgetConfig(str(planner["strategy"]), candidate_count, max_repairs)

    execution = raw.get("execution")
    if not isinstance(execution, dict):
        raise ConfigError("execution must be an object")
    _check_fields(execution, {"timeout_seconds", "environment"}, "execution")
    timeout = execution.get("timeout_seconds")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ConfigError("timeout_seconds must be positive")
    environment = execution.get("environment", {})
    if not isinstance(environment, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in environment.items()):
        raise ConfigError("environment must be a string map")
    execution_config = ExecutionConfig(float(timeout), dict(environment))

    evaluator = raw.get("evaluator")
    if not isinstance(evaluator, dict):
        raise ConfigError("evaluator must be an object")
    _check_fields(evaluator, {"strategy", "version"}, "evaluator")
    if not isinstance(evaluator.get("strategy"), str) or not evaluator["strategy"].strip():
        raise ConfigError("evaluator.strategy must be a non-empty string")
    evaluator_config = EvaluatorConfig(str(evaluator["strategy"]), str(evaluator.get("version", "benchmark_f2p_v1")))

    target = raw.get("target", {})
    if not isinstance(target, dict):
        raise ConfigError("target must be an object")
    _check_fields(target, {"buggy_checkout", "fixed_checkout", "python", "runner", "source_path_markers"}, "target")
    artifact_root = raw.get("artifact_root", "artifacts/runs")
    paths = RunPaths(_path(raw["target_context"], config_path, root), _path(raw["structured_history"], config_path, root), _path(raw["frozen_hypotheses"], config_path, root), _path(str(artifact_root), config_path, root), _path(raw["target_manifest"], config_path, root) if raw.get("target_manifest") else None)
    config_hash = stable_hash(raw)
    return RunConfig(SCHEMA_VERSION, raw["run_id"], raw["target_id"], raw["target_context"], raw["structured_history"], raw["frozen_hypotheses"], model_config, planner_config, execution_config, evaluator_config, paths, dict(target), config_hash)
