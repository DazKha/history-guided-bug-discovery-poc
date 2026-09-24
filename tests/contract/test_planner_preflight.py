import pytest

from history_guided_bug_discovery.application.test_generation_service import preflight_test_source
from history_guided_bug_discovery.application.planning_service import parse_plan_response, validate_trigger_plan


def valid_plan():
    return {
        "hypothesis_id": "h1",
        "preconditions": ["public API is importable"],
        "initial_state": {"output_path": "temporary path"},
        "actions": [
            {"type": "initialize_state", "description": "create state"},
            {"type": "invoke", "description": "call public API"},
            {"type": "observe", "description": "read output"},
        ],
        "expected_invariant": "the output preserves the value",
        "observable": {"source": "public API output", "measurement_point": "after invoke", "extraction_method": "read output"},
        "assertion": {"predicate": "output contains value", "failure_condition": "value absent", "rationale": "measures output"},
        "setup": ["create temporary path"],
        "timeout_seconds": 30,
    }


def test_planner_contract_rejects_wrong_order_and_leakage():
    plan = valid_plan()
    plan["actions"] = [plan["actions"][2], plan["actions"][1]]
    with pytest.raises(ValueError, match="invoke|observe"):
        validate_trigger_plan(plan, "h1", "public API output")
    plan = valid_plan()
    plan["setup"] = ["inspect fixed revision"]
    with pytest.raises(ValueError, match="leakage"):
        validate_trigger_plan(plan, "h1", "public API output")


def test_preflight_rejects_syntax_assertion_and_hidden_access():
    with pytest.raises(ValueError, match="syntax"):
        preflight_test_source("def test_broken(:\n    pass\n")
    with pytest.raises(ValueError, match="assertion"):
        preflight_test_source("def test_no_assert():\n    return None\n")
    with pytest.raises(ValueError, match="forbidden"):
        preflight_test_source("def test_hidden():\n    assert open('bug_patch.txt').read()\n")
    with pytest.raises(ValueError, match="forbidden"):
        preflight_test_source("def test_forced():\n    assert False\n")


def test_preflight_accepts_meaningful_pytest_module():
    source = "def test_value():\n    observed = 1\n    assert observed == 1\n"
    assert preflight_test_source(source) == source


def test_planner_parser_rejects_malformed_missing_duplicate_and_misaligned_plans():
    with pytest.raises(ValueError, match="malformed JSON"):
        parse_plan_response("{", "h1")
    incomplete = valid_plan()
    del incomplete["observable"]
    with pytest.raises(ValueError, match="missing required"):
        parse_plan_response('{"plans": [' + __import__("json").dumps(incomplete) + ']}', "h1")
    unsupported = valid_plan()
    unsupported["actions"][0]["type"] = "inspect_fixed_revision"
    with pytest.raises(ValueError, match="unsupported action"):
        parse_plan_response('{"plans": [' + __import__("json").dumps(unsupported) + ']}', "h1", "public API output")
    duplicate = __import__("json").dumps({"plans": [valid_plan(), valid_plan()]})
    with pytest.raises(ValueError, match="duplicates"):
        parse_plan_response(duplicate, "h1", "public API output")
    misaligned = valid_plan()
    misaligned["assertion"] = {"predicate": "unrelated thing", "failure_condition": "other thing", "rationale": "different measure"}
    with pytest.raises(ValueError, match="assertion"):
        parse_plan_response('{"plans": [' + __import__("json").dumps(misaligned) + ']}', "h1", "public API output")
