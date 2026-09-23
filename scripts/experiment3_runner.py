from __future__ import annotations

import copy
import hashlib
import json
from typing import Any


def freeze_hypothesis(record: dict[str, Any]) -> dict[str, Any]:
    frozen = copy.deepcopy(record)
    frozen["hypothesis_frozen"] = True
    frozen["hypothesis_sha256"] = hashlib.sha256(
        json.dumps({key: frozen.get(key) for key in ("hypothesis", "trigger", "potential_failure", "oracle")}, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return frozen


def hypothesis_prompt(hypothesis: dict[str, Any]) -> str:
    visible = {key: hypothesis.get(key, "") for key in ("hypothesis_id", "hypothesis", "trigger", "potential_failure", "oracle")}
    return f"""Generate exactly one complete pytest module from this frozen hypothesis.
Do not change the claim, mechanism, expected behavior, oracle, or target evidence. Use only public target APIs and the target context already supplied when the hypothesis was created. The test must be deterministic, executable, and use a meaningful assertion. Do not use hidden metadata, fixed revisions, issue text, or benchmark paths. Return JSON only with status TEST or NO_SUPPORTED_HYPOTHESIS and test_code.

FROZEN HYPOTHESIS:
{json.dumps(visible, ensure_ascii=False, indent=2)}
"""


def test_prompt(hypothesis: dict[str, Any], trigger: dict[str, Any], target_context: str) -> str:
    visible = {key: hypothesis.get(key, "") for key in ("hypothesis_id", "hypothesis", "trigger", "potential_failure", "oracle")}
    return f"""Generate one complete deterministic pytest module that instantiates the frozen hypothesis through the trigger plan.

Keep the hypothesis and oracle unchanged. Use only the target context, public APIs, and the trigger plan. Do not inspect fixed source, issue reports, diffs, hidden regression tests, or benchmark metadata. The test must reach the listed preconditions, perform the action sequence, and assert the listed observable without manufacturing failure. Return JSON only with status TEST or NO_SUPPORTED_HYPOTHESIS and test_code.

FROZEN HYPOTHESIS:
{json.dumps(visible, ensure_ascii=False, indent=2)}
TRIGGER PLAN:
{json.dumps(trigger, ensure_ascii=False, indent=2)}
TARGET CONTEXT:
{target_context}
"""


def parse_test_response(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = text.replace("```json", "", 1).replace("```", "").strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("test response did not contain a JSON object")
    obj = json.loads(text[start:end + 1])
    status = str(obj.get("status", "")).upper()
    if status in {"HYPOTHESIS", "SUPPORTED", "TEST"}:
        status = "TEST"
    elif status in {"NO_SUPPORTED_HYPOTHESIS", "NO_HYPOTHESIS", "ABSTAIN"}:
        status = "NO_SUPPORTED_HYPOTHESIS"
    else:
        raise ValueError(f"unsupported test status: {status}")
    code = str(obj.get("test_code") or "")
    if status == "TEST":
        lowered = code.lower()
        if not code or any(token in lowered for token in ("assert false", "pytest.fail", "git show", "bugsinpy", "test_chinese.py")):
            raise ValueError("test output is empty or contains forbidden construction")
    return {"status": status, "test_code": code}
