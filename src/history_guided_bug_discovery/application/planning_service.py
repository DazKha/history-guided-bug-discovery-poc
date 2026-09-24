from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from typing import Any

from ..config.models import RunConfig
from ..domain.errors import SchemaValidationError
from ..domain.models import FrozenHypothesis, HistoricalBugUnit, TriggerPlan
from ..ports.llm import GenerationRequest, GenerationResponse, LLMProvider
from .prompts import strict_trigger_plan_v1

PLAN_FIELDS = {"hypothesis_id", "preconditions", "initial_state", "actions", "expected_invariant", "observable", "assertion", "setup", "timeout_seconds"}
OBSERVABLE_FIELDS = {"source", "measurement_point", "extraction_method"}
ASSERTION_FIELDS = {"predicate", "failure_condition", "rationale"}
ACTION_FIELDS = {"type", "description"}
ACTION_TYPES = {"create_input", "set_environment", "initialize_state", "invoke", "observe"}
LEAKAGE_TERMS = {"fixed revision", "fixed checkout", "fixed source", "developer patch", "issue report", "issue text", "hidden test", "target issue", "evaluator verdict", "evaluator result", "changed lines", "benchmark metadata", "bug_patch.txt", "test_chinese.py"}
STOPWORDS = {"a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "it", "must", "of", "on", "or", "the", "to", "with"}


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SchemaValidationError(f"{field} must be a non-empty string")
    return value.strip()


def _string_list(value: Any, field: str, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise SchemaValidationError(f"{field} must be a non-empty list of strings")
    return [_text(item, f"{field}[{index}]") for index, item in enumerate(value)]


def _tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[A-Za-z_][A-Za-z0-9_.-]{2,}", value.lower()) if token not in STOPWORDS}


def _contains_leakage(value: Any) -> bool:
    text = json.dumps(value, ensure_ascii=False).lower()
    return any(term in text for term in LEAKAGE_TERMS)


def validate_trigger_plan(plan: dict[str, Any], hypothesis_id: str, target_context: str = "") -> dict[str, Any]:
    if not isinstance(plan, dict):
        raise SchemaValidationError("plan must be a JSON object")
    errors: list[str] = []
    unknown = sorted(set(plan) - PLAN_FIELDS)
    missing = sorted(PLAN_FIELDS - set(plan))
    if unknown:
        errors.append("unknown plan fields: " + ", ".join(unknown))
    if missing:
        errors.append("plan missing required fields: " + ", ".join(missing))
    if errors:
        raise SchemaValidationError("; ".join(errors))
    result = copy.deepcopy(plan)
    if result["hypothesis_id"] != hypothesis_id:
        errors.append("hypothesis_id does not match frozen hypothesis")
    try:
        result["expected_invariant"] = _text(result["expected_invariant"], "expected_invariant")
    except SchemaValidationError as exc:
        errors.append(str(exc))
    for field in ("preconditions", "setup"):
        try:
            result[field] = _string_list(result[field], field, allow_empty=field == "setup")
        except SchemaValidationError as exc:
            errors.append(str(exc))
    if not isinstance(result["initial_state"], dict) or not result["initial_state"]:
        errors.append("initial_state must identify at least one state value")

    actions = result["actions"]
    normalized_actions: list[dict[str, str]] = []
    if not isinstance(actions, list) or not actions:
        errors.append("actions must be a non-empty list")
    else:
        for index, action in enumerate(actions):
            if not isinstance(action, dict):
                errors.append(f"actions[{index}] must be an object")
                continue
            action_missing = sorted(ACTION_FIELDS - set(action))
            action_unknown = sorted(set(action) - ACTION_FIELDS)
            if action_missing:
                errors.append(f"actions[{index}] missing required fields: {', '.join(action_missing)}")
            if action_unknown:
                errors.append(f"actions[{index}] unknown fields: {', '.join(action_unknown)}")
            if action_missing:
                continue
            action_type = str(action["type"]).strip().lower()
            if action_type not in ACTION_TYPES:
                errors.append(f"unsupported action type: {action_type}")
            try:
                description = _text(action["description"], f"actions[{index}].description")
            except SchemaValidationError as exc:
                errors.append(str(exc))
                description = ""
            normalized_actions.append({"type": action_type, "description": description})
        result["actions"] = normalized_actions
        invokes = [i for i, action in enumerate(normalized_actions) if action["type"] == "invoke"]
        observes = [i for i, action in enumerate(normalized_actions) if action["type"] == "observe"]
        if not invokes:
            errors.append("actions must contain an invoke action")
        if not observes:
            errors.append("actions must contain an observe action")
        if invokes and observes and min(observes) <= min(invokes):
            errors.append("observe action must occur after invoke action")

    observable = result["observable"]
    if not isinstance(observable, dict):
        errors.append("observable must be an object")
        observable = {}
    else:
        missing_obs = sorted(OBSERVABLE_FIELDS - set(observable))
        unknown_obs = sorted(set(observable) - OBSERVABLE_FIELDS)
        if missing_obs:
            errors.append("observable missing required fields: " + ", ".join(missing_obs))
        if unknown_obs:
            errors.append("observable unknown fields: " + ", ".join(unknown_obs))
        for field in OBSERVABLE_FIELDS:
            if field in observable:
                try:
                    observable[field] = _text(observable[field], f"observable.{field}")
                except SchemaValidationError as exc:
                    errors.append(str(exc))
        result["observable"] = observable
        if target_context and isinstance(observable.get("source"), str) and _tokens(observable["source"]) and not _tokens(observable["source"]).intersection(_tokens(target_context)):
            errors.append("observable.source has no statically supported target-context token")

    assertion = result["assertion"]
    if not isinstance(assertion, dict):
        errors.append("assertion must be an object")
        assertion = {}
    else:
        missing_assert = sorted(ASSERTION_FIELDS - set(assertion))
        unknown_assert = sorted(set(assertion) - ASSERTION_FIELDS)
        if missing_assert:
            errors.append("assertion missing required fields: " + ", ".join(missing_assert))
        if unknown_assert:
            errors.append("assertion unknown fields: " + ", ".join(unknown_assert))
        for field in ASSERTION_FIELDS:
            if field in assertion:
                try:
                    assertion[field] = _text(assertion[field], f"assertion.{field}")
                except SchemaValidationError as exc:
                    errors.append(str(exc))
        result["assertion"] = assertion
        expected = _tokens(result.get("expected_invariant", ""))
        observed = _tokens(" ".join(str(observable.get(field, "")) for field in OBSERVABLE_FIELDS))
        asserted = _tokens(" ".join(str(assertion.get(field, "")) for field in ASSERTION_FIELDS))
        if expected and observed and not asserted.intersection(expected | observed):
            errors.append("assertion is not lexically aligned with expected_invariant or observable")

    timeout = result["timeout_seconds"]
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 1 <= timeout <= 120:
        errors.append("timeout_seconds must be a number between 1 and 120")
    else:
        result["timeout_seconds"] = float(timeout)
    if _contains_leakage(result):
        errors.append("leakage control: plan contains forbidden evaluator or hidden-target terminology")
    if errors:
        raise SchemaValidationError("; ".join(errors))
    return result


def parse_plan_response(content: str, hypothesis_id: str, target_context: str = "", limit: int = 3) -> list[dict[str, Any]]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SchemaValidationError(f"malformed JSON: {exc.msg} at line {exc.lineno} column {exc.colno}") from exc
    if not isinstance(obj, dict) or set(obj) != {"plans"} or not isinstance(obj["plans"], list):
        raise SchemaValidationError("response must contain exactly one plans list")
    if not 1 <= len(obj["plans"]) <= limit:
        raise SchemaValidationError(f"plans must contain between 1 and {limit} entries")
    plans: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, plan in enumerate(obj["plans"]):
        validated = validate_trigger_plan(plan, hypothesis_id, target_context)
        key = json.dumps(validated, sort_keys=True, ensure_ascii=False)
        if key in seen:
            raise SchemaValidationError(f"plans[{index}] duplicates another plan")
        seen.add(key)
        plans.append(validated)
    return plans


@dataclass(frozen=True)
class PlanningResult:
    plans: tuple[TriggerPlan, ...]
    attempts: tuple[dict[str, Any], ...]
    responses: tuple[GenerationResponse, ...]


class PlanningService:
    def __init__(self, provider: LLMProvider, config: RunConfig):
        self.provider = provider
        self.config = config

    def generate(self, hypothesis: FrozenHypothesis, target_context: str, history: tuple[HistoricalBugUnit, ...]) -> PlanningResult:
        attempts: list[dict[str, Any]] = []
        responses: list[GenerationResponse] = []
        feedback = ""
        for attempt in range(self.config.planner.max_repairs + 1):
            prompt = strict_trigger_plan_v1(hypothesis, target_context, history, self.config.planner.candidate_count, feedback)
            request = GenerationRequest(self.config.run_id, f"planner-{hypothesis.hypothesis_id}-{attempt}", "strict_trigger_plan_v1", prompt, self.config.model.name, self.config.model.temperature, self.config.model.max_output_tokens, self.config.model.timeout_seconds, self.config.model.response_format, self.config.model.thinking)
            try:
                response = self.provider.generate(request)
                responses.append(response)
                plans = parse_plan_response(response.content, hypothesis.hypothesis_id, target_context, self.config.planner.candidate_count)
                attempts.append({"attempt": attempt, "status": "VALID", "prompt_hash": request.prompt_hash, "usage": dict(response.usage)})
                return PlanningResult(tuple(TriggerPlan.create(self.config.run_id, hypothesis.hypothesis_id, f"plan-{index}", plan, request.prompt_hash) for index, plan in enumerate(plans, 1)), tuple(attempts), tuple(responses))
            except Exception as exc:
                attempts.append({"attempt": attempt, "status": "INVALID", "error": str(exc)[:1000], "prompt_hash": request.prompt_hash})
                feedback = f"Your previous response failed deterministic validation: {str(exc)[:1000]}. Repair only the JSON/schema/sequence/assertion alignment. Keep the frozen hypothesis unchanged. Return JSON only."
        return PlanningResult((), tuple(attempts), tuple(responses))
