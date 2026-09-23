import pytest

from scripts.experiment4_plan_contract import parse_plan_response, validate_plan


def valid_plan():
    return {
        "hypothesis_id": "h1",
        "preconditions": ["The public decorator is importable"],
        "initial_state": {"output_path": "a temporary path"},
        "actions": [
            {"type": "set_environment", "description": "Set a controlled locale"},
            {"type": "invoke", "description": "Call the decorated function"},
            {"type": "observe", "description": "Read the trace output"},
        ],
        "expected_invariant": "The trace output preserves the observed value",
        "observable": {
            "source": "FileWriter.write output path",
            "measurement_point": "after the decorated function returns",
            "extraction_method": "read the output file as UTF-8",
        },
        "assertion": {
            "predicate": "the observed trace contains the preserved value",
            "failure_condition": "the value is absent or the call raises",
            "rationale": "the predicate measures the expected invariant at the observation point",
        },
        "setup": ["Create a temporary output path"],
        "timeout_seconds": 30,
    }


def test_valid_plan_is_normalized_and_requires_invoke_before_observe():
    result = validate_plan(valid_plan(), "h1", target_context="FileWriter.write output path")
    assert result["hypothesis_id"] == "h1"
    assert result["actions"][1]["type"] == "invoke"


def test_invalid_plan_reports_multiple_deterministic_errors():
    plan = valid_plan()
    plan["actions"] = [{"type": "observe", "description": "observe"}]
    plan["assertion"]["predicate"] = "unrelated condition"
    with pytest.raises(ValueError, match="invoke action|assertion"):
        validate_plan(plan, "h1", target_context="FileWriter.write output path")


def test_unsupported_action_and_missing_observable_are_rejected():
    plan = valid_plan()
    plan["actions"][0]["type"] = "inspect_fixed_revision"
    plan["observable"]["source"] = ""
    with pytest.raises(ValueError, match="unsupported action|observable.source"):
        validate_plan(plan, "h1", target_context="FileWriter.write output path")


def test_parser_accepts_only_a_plans_object_and_validates_shape():
    content = '{"plans": [' + __import__("json").dumps(valid_plan()) + ']}'
    plans = parse_plan_response(content, "h1", "FileWriter.write output path")
    assert len(plans) == 1
    assert plans[0]["hypothesis_id"] == "h1"
