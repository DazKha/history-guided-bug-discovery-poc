from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from ..domain.models import FrozenHypothesis, HistoricalBugUnit


def _visible(hypothesis: FrozenHypothesis) -> dict[str, Any]:
    return {"hypothesis_id": hypothesis.hypothesis_id, "hypothesis": hypothesis.claim, "trigger": hypothesis.trigger, "potential_failure": hypothesis.potential_failure, "oracle": dict(hypothesis.oracle)}


def direct_test_v1(hypothesis: FrozenHypothesis) -> str:
    return f"""Generate exactly one complete pytest module from this frozen hypothesis.
Do not change the claim, mechanism, expected behavior, oracle, or target evidence. Use only public target APIs and the target context already supplied when the hypothesis was created. The test must be deterministic, executable, and use a meaningful assertion. Do not use hidden metadata, fixed revisions, issue text, or benchmark paths. Return JSON only with status TEST or NO_SUPPORTED_HYPOTHESIS and test_code.

FROZEN HYPOTHESIS:
{json.dumps(_visible(hypothesis), ensure_ascii=False, indent=2)}
"""


def strict_trigger_plan_v1(hypothesis: FrozenHypothesis, target_context: str, history: Sequence[HistoricalBugUnit], candidate_count: int, feedback: str = "") -> str:
    schema = {"hypothesis_id": "same frozen id", "preconditions": ["concrete condition"], "initial_state": {"named_state": "value or condition"}, "actions": [{"type": "create_input|set_environment|initialize_state|invoke|observe", "description": "concrete action"}], "expected_invariant": "one observable expected behavior", "observable": {"source": "public target source or API named in context", "measurement_point": "when measured", "extraction_method": "how value is read"}, "assertion": {"predicate": "what is asserted", "failure_condition": "what meaningful failure means", "rationale": "why this measures the invariant"}, "setup": ["required setup"], "timeout_seconds": 30}
    return f"""You are a constrained trigger-plan generator in a controlled software-testing experiment.

The mechanism hypothesis is frozen. Do not revise, broaden, or replace it. Generate exactly {candidate_count} meaningfully different executable plans for that same hypothesis. Diversity must change a supported input boundary, state setup, environment, sequence, or public interface path; changing only a character is not diversity. Only use dimensions supported by the hypothesis and the visible buggy target context. Do not use fixed source, patches, issue text, hidden regression tests, evaluator verdicts, or benchmark metadata.

Return JSON only with exactly one top-level key, `plans`, whose value is a list of 1 to {candidate_count} plan objects. Every plan must contain exactly the fields and nested fields shown below. Actions are ordered. Use only these action types: create_input, set_environment, initialize_state, invoke, observe. Every plan must contain an invoke action followed by an observe action. The assertion must measure the observable at the stated measurement point and must not be a generic unconditional failure.

SCHEMA:
{json.dumps(schema, ensure_ascii=False, indent=2)}

FROZEN HYPOTHESIS:
{json.dumps(_visible(hypothesis), ensure_ascii=False, indent=2)}

TARGET CONTEXT (buggy checkout only):
{target_context}

STRUCTURED HISTORY ALREADY USED TO FORM THE HYPOTHESIS:
{json.dumps([item.to_dict() for item in history], ensure_ascii=False, indent=2)}

{feedback}
"""


def plan_to_test_compact_v1(hypothesis: FrozenHypothesis, plan: Mapping[str, Any], target_context: str) -> str:
    return f"""Generate one compact, complete pytest module from this frozen hypothesis and validated plan.
Return exactly one JSON object with status TEST and test_code, with no markdown or explanation. Keep the hypothesis and oracle unchanged. Use only public APIs and the supplied buggy target context; never use fixed source, patches, issue text, hidden tests, evaluator results, or benchmark paths. Define every name in each module/subprocess scope, declare fixtures, use relative temporary paths, and capture/decode subprocess bytes before comparing text. Execute setup, invoke, observe, then assert the stated invariant. Do not force failure or assert an unrelated value.

FROZEN HYPOTHESIS:
{json.dumps(_visible(hypothesis), ensure_ascii=False, separators=(',', ':'))}
VALIDATED PLAN:
{json.dumps(plan, ensure_ascii=False, separators=(',', ':'))}
TARGET CONTEXT:
{target_context}
"""
