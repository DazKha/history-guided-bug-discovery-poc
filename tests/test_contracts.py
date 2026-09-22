import json
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_structured_history_contract(tmp_path):
    from scripts.prepare_data import REQUIRED_HISTORY_FIELDS, validate_history_records

    record = {
        "history_id": "example:1",
        **{field: {"text": "evidence", "provenance": "direct"} for field in REQUIRED_HISTORY_FIELDS},
    }
    assert validate_history_records([record]) == []


def test_target_context_redacts_evaluator_files(tmp_path):
    from scripts.prepare_data import build_target_context

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "safe.py").write_text("def f():\n    return 1\n")
    (repo / "bugsinpy_bug.info").write_text("fixed_commit_id='secret'\n")
    (repo / "tests").mkdir()
    (repo / "tests/test_hidden.py").write_text("assert 'hidden issue'\n")
    context = build_target_context(repo, excluded_paths={"tests/test_hidden.py"})
    assert "safe.py" in context
    assert "secret" not in context
    assert "hidden issue" not in context


def test_client_redacts_key_and_records_usage(monkeypatch):
    from scripts.deepseek_client import DeepSeekClient

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "model": "deepseek-flash",
                "choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 4, "completion_tokens": 3, "total_tokens": 7},
            }

    monkeypatch.setattr("scripts.deepseek_client.requests.post", lambda *a, **k: Response())
    client = DeepSeekClient(api_key="secret-value", model="deepseek-flash")
    result = client.generate("hello", max_tokens=16)
    assert result.content == "{}"
    assert result.usage["total_tokens"] == 7
    assert "secret-value" not in json.dumps(result.log_record)


def test_outcome_classifier_counts_only_semantic_assertion():
    from scripts.evaluate_generated_tests import classify_pair

    assert classify_pair(1, "AssertionError: expected invariant", 0, "", "h") == "F2P"
    assert classify_pair(1, "ModuleNotFoundError: x", 0, "", "h") == "MECHANICAL_FAILURE"
    assert classify_pair(0, "", 1, "AssertionError: x", "h") == "P2F"


def test_condition_c_allows_no_supported_hypothesis():
    from scripts.run_experiment import parse_model_output

    parsed = parse_model_output('{"status":"NO_SUPPORTED_HYPOTHESIS","applicability":[]}')
    assert parsed["status"] == "NO_SUPPORTED_HYPOTHESIS"
