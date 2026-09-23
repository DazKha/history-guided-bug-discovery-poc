from __future__ import annotations

import copy
import json
import re
from typing import Any


TRIGGER_TYPES = {"INPUT", "STATE", "ENVIRONMENT", "SEQUENCE", "CONCURRENCY", "RETRY"}
REQUIRED_FIELDS = {
    "trigger_id", "hypothesis_id", "trigger_type", "mechanism", "preconditions",
    "input_mutation", "state_setup", "environment_setup", "action_sequence",
    "observable", "why_this_may_expose_the_mechanism", "target_evidence", "confidence",
}


def validate_trigger(candidate: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(REQUIRED_FIELDS - set(candidate))
    if missing:
        raise ValueError(f"trigger missing required fields: {', '.join(missing)}")
    trigger_type = str(candidate["trigger_type"]).upper().strip()
    if trigger_type not in TRIGGER_TYPES:
        raise ValueError(f"unsupported trigger_type: {trigger_type}")
    result = copy.deepcopy(candidate)
    result["trigger_type"] = trigger_type
    for field in ("preconditions", "action_sequence", "target_evidence"):
        value = result[field]
        if not isinstance(value, list) or not all(str(item).strip() for item in value):
            raise ValueError(f"{field} must be a non-empty list of strings")
        result[field] = [str(item).strip() for item in value]
    for field in ("mechanism", "input_mutation", "state_setup", "environment_setup", "observable", "why_this_may_expose_the_mechanism"):
        result[field] = str(result[field]).strip()
        if not result[field]:
            raise ValueError(f"{field} must be non-empty")
    try:
        result["confidence"] = float(result["confidence"])
    except (TypeError, ValueError) as exc:
        raise ValueError("confidence must be numeric") from exc
    if not 0 <= result["confidence"] <= 1:
        raise ValueError("confidence must be between 0 and 1")
    return result


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value).strip().lower())


def _diversity_key(trigger: dict[str, Any]) -> tuple[str, ...]:
    return (
        _norm(trigger["trigger_type"]),
        _norm(trigger["input_mutation"]),
        _norm(trigger["state_setup"]),
        _norm(trigger["environment_setup"]),
        _norm(trigger["action_sequence"]),
        _norm(trigger["observable"]),
    )


def deduplicate_triggers(candidates: list[dict[str, Any]], limit: int = 4) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()
    for raw in candidates:
        trigger = validate_trigger(raw)
        key = _diversity_key(trigger)
        if key in seen:
            continue
        seen.add(key)
        selected.append(trigger)
        if len(selected) >= limit:
            break
    return selected


def build_trigger_prompt(hypothesis: dict[str, Any], target_context: str, history: list[dict[str, Any]], count: int = 4) -> str:
    frozen = json.dumps(hypothesis, ensure_ascii=False, indent=2)
    historical = json.dumps(history, ensure_ascii=False, indent=2)
    return f"""You are a trigger planner for a controlled software-testing experiment.

Use only the ordinary target context, the structured historical evidence, and the frozen hypothesis below.
The hypothesis is frozen: do not change its mechanism, expected behavior, oracle, or claim.
Generate exactly {count} meaningfully different trigger candidates. A meaningful difference changes an input boundary, state setup, environment, action sequence, concurrency/retry condition, or public interface path; merely swapping similar characters is not diversity.
Only use a trigger dimension when supported by the hypothesis and target context. Do not invent hidden bug facts.
Allowed trigger_type values: INPUT, STATE, ENVIRONMENT, SEQUENCE, CONCURRENCY, RETRY.
Return JSON only: {{"triggers": [{{"trigger_id": "...", "hypothesis_id": "...", "trigger_type": "...", "mechanism": "...", "preconditions": ["..."], "input_mutation": "...", "state_setup": "...", "environment_setup": "...", "action_sequence": ["..."], "observable": "...", "why_this_may_expose_the_mechanism": "...", "target_evidence": ["..."], "confidence": 0.0}}]}}

===== FROZEN HYPOTHESIS =====
{frozen}
===== TARGET CONTEXT =====
{target_context}
===== STRUCTURED HISTORY =====
{historical}
"""


def parse_trigger_response(content: str) -> list[dict[str, Any]]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("trigger response did not contain a JSON object")
    obj = json.loads(text[start:end + 1])
    triggers = obj.get("triggers")
    if not isinstance(triggers, list):
        raise ValueError("trigger response must contain a triggers list")
    return deduplicate_triggers(triggers, limit=4)

