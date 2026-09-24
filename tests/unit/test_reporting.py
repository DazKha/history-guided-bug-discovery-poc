from history_guided_bug_discovery.domain.enums import Arm
from pathlib import Path

from history_guided_bug_discovery.reporting.aggregate import aggregate_rows, validate_consistency, validate_report_files
from history_guided_bug_discovery.reporting.csv_report import write_csv
from history_guided_bug_discovery.reporting.markdown import write_markdown


def test_aggregate_rejects_impossible_candidate_totals():
    rows = [{"stage": "TEST", "classification": "P2P", "test_status": "EXECUTABLE", "llm_calls": "1", "prompt_tokens": "1", "completion_tokens": "1"}]
    summary = aggregate_rows(rows, Arm.DIRECT)
    validate_consistency(summary)
    summary.model_output_failures = 1
    try:
        validate_consistency(summary)
    except ValueError as exc:
        assert "candidate outcome" in str(exc)
    else:
        raise AssertionError("inconsistent summary was accepted")


def test_csv_json_markdown_reports_agree(tmp_path):
    summary = aggregate_rows([{"stage": "TEST", "classification": "P2P", "test_status": "EXECUTABLE", "llm_calls": "1", "prompt_tokens": "2", "completion_tokens": "3"}], Arm.DIRECT)
    json_path = tmp_path / "summary.json"
    csv_path = tmp_path / "summary.csv"
    md_path = tmp_path / "summary.md"
    import json
    json_path.write_text(json.dumps(summary.to_dict()))
    write_csv(summary, csv_path)
    write_markdown(summary, md_path)
    assert validate_report_files(json_path, csv_path, md_path) is True
