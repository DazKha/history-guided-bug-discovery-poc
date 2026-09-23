from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_trigger_schema_accepts_supported_types_and_requires_fields():
    from scripts.experiment3_trigger_planner import validate_trigger

    candidate = {
        "trigger_id": "h1-t1",
        "hypothesis_id": "h1",
        "trigger_type": "ENVIRONMENT",
        "mechanism": "implicit encoding depends on environment",
        "preconditions": ["target reads a UTF-8 file"],
        "input_mutation": "use one non-ASCII value",
        "state_setup": "create a temporary source file",
        "environment_setup": "set a non-UTF-8 locale",
        "action_sequence": ["invoke the public API", "inspect output"],
        "observable": "output preserves the source value",
        "why_this_may_expose_the_mechanism": "the precondition is exercised",
        "target_evidence": ["target source and ordinary docs"],
        "confidence": 0.7,
    }

    normalized = validate_trigger(candidate)
    assert normalized["trigger_type"] == "ENVIRONMENT"
    assert normalized["confidence"] == 0.7

    with pytest.raises(ValueError):
        validate_trigger({"trigger_id": "bad", "trigger_type": "MAGIC"})


def test_trigger_diversity_deduplicates_same_dimension():
    from scripts.experiment3_trigger_planner import deduplicate_triggers

    base = {
        "hypothesis_id": "h1",
        "mechanism": "state-sensitive behavior",
        "preconditions": ["state is initialized"],
        "input_mutation": "same input",
        "state_setup": "same setup",
        "environment_setup": "same environment",
        "action_sequence": ["call once"],
        "observable": "same observable",
        "why_this_may_expose_the_mechanism": "same reason",
        "target_evidence": ["target.py:10"],
        "confidence": 0.5,
    }
    candidates = [
        {**base, "trigger_id": "t1", "trigger_type": "INPUT"},
        {**base, "trigger_id": "t2", "trigger_type": "INPUT"},
        {**base, "trigger_id": "t3", "trigger_type": "SEQUENCE", "action_sequence": ["call twice"]},
    ]

    selected = deduplicate_triggers(candidates, limit=4)
    assert [item["trigger_id"] for item in selected] == ["t1", "t3"]


def test_trigger_prompt_has_no_evaluator_only_inputs():
    from scripts.experiment3_trigger_planner import build_trigger_prompt

    prompt = build_trigger_prompt(
        {"hypothesis_id": "h1", "hypothesis": "a frozen claim", "oracle": "a target-supported invariant"},
        "ordinary target context",
        [{"history_id": "cookiecutter:1", "Failure Mechanism": "encoding"}],
        count=4,
    )
    lowered = prompt.lower()
    assert "fixed checkout" not in lowered
    assert "bug patch" not in lowered
    assert "evaluator truth" not in lowered
    assert "exactly 4" in lowered


def test_freeze_hypothesis_preserves_text_and_marks_record():
    from scripts.experiment3_runner import freeze_hypothesis

    record = {"hypothesis": "immutable claim", "oracle": {"expected_behavior": "preserve value"}}
    frozen = freeze_hypothesis(record)
    assert frozen["hypothesis_frozen"] is True
    assert frozen["hypothesis"] == record["hypothesis"]
    assert frozen["oracle"] == record["oracle"]
    frozen["oracle"]["expected_behavior"] = "changed locally"
    assert record["oracle"]["expected_behavior"] == "preserve value"


def test_generation_prompts_expose_only_frozen_hypothesis_fields():
    from scripts.experiment3_runner import hypothesis_prompt, test_prompt

    hypothesis = {
        "hypothesis_id": "h1",
        "hypothesis": "claim",
        "trigger": "setup",
        "potential_failure": "failure",
        "oracle": {"expected_behavior": "invariant"},
        "source_artifact": "artifacts/evaluator_only/truth.json",
        "hypothesis_matches_true_failure_mechanism": "yes",
    }
    direct = hypothesis_prompt(hypothesis)
    planned = test_prompt(hypothesis, {"trigger_id": "t1"}, "context")
    assert "truth.json" not in direct
    assert "mechanism_match" not in direct
    assert "truth.json" not in planned
    assert "mechanism_match" not in planned


def test_metrics_emits_one_row_per_trigger_test_pair():
    from scripts.experiment3_metrics import expand_trigger_rows

    rows = expand_trigger_rows(
        {"hypothesis_id": "h1", "mechanism_match": "yes"},
        [
            {"trigger_id": "t1", "test_id": "x1", "classification": "P2P"},
            {"trigger_id": "t2", "test_id": "x2", "classification": "F2P"},
        ],
    )
    assert [row["trigger_id"] for row in rows] == ["t1", "t2"]
    assert all(row["hypothesis_id"] == "h1" for row in rows)
