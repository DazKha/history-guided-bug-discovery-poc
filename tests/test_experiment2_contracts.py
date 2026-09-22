import json
from pathlib import Path

from scripts.run_experiment2 import parse_model, prompt_for


ROOT = Path(__file__).resolve().parents[1]


def test_transfer_case_and_leakage_manifest_are_separated():
    candidates = json.loads((ROOT / "data/transfer_case_candidates.json").read_text())
    manifest = json.loads((ROOT / "data/target_leakage_manifest.json").read_text())
    assert manifest["selected_history_ids"] == ["cookiecutter:1", "PySnooper:3"]
    assert candidates["chosen_candidate"]["historical_bugs"] == manifest["selected_history_ids"]
    assert manifest["evaluator_only"]["truth_file"] not in manifest["agent_visible"].values()
    assert "tests/test_chinese.py" not in (ROOT / manifest["agent_visible"]["target_context"]).read_text()


def test_condition_prompts_keep_history_and_abstention_controls_distinct():
    context = "TARGET_CONTEXT"
    raw = [{"history_id": "cookiecutter:1", "fix_diff": "encoding='utf-8'"}]
    structured = [{"history_id": "cookiecutter:1", "Failure Mechanism": "explicit UTF-8"}]
    a = prompt_for("A", context, raw, structured, 1)
    b = prompt_for("B", context, raw, structured, 1)
    c = prompt_for("C", context, raw, structured, 1)
    assert "NO HISTORICAL EVIDENCE" in a
    assert "RAW HISTORICAL BUG EVIDENCE" in b
    assert "STRUCTURED HISTORICAL BUG KNOWLEDGE" in c
    assert "Do not apply an explicit applicability gate" in b
    assert "SUPPORTED, WEAK, or NOT_APPLICABLE" in c
    assert "fix_diff" not in a


def test_parser_canonicalizes_test_and_no_support():
    test = parse_model('{"status":"HYPOTHESIS","hypothesis":"h","trigger":"t","potential_failure":"p","oracle":{"expected_behavior":"e"},"test_code":"def test_x():\\n    assert 1 == 1"}')
    abstain = parse_model('{"status":"NOT_APPLICABLE","applicability_decisions":["not applicable"]}')
    assert test["status"] == "TEST"
    assert abstain["status"] == "NO_SUPPORTED_HYPOTHESIS"
