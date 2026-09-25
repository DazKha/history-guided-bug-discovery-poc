from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_required_artifacts_exist():
    required = [
        "README.md",
        "research_log.md",
        "data/case_manifest.json",
        "data/historical_raw.json",
        "data/historical_structured.json",
        "results/results.csv",
        "results/summary.csv",
        "results/failure_analysis.md",
        "FOLLOWUP_REPORT.md",
        "prompts/target_only.txt",
        "prompts/raw_history.txt",
        "prompts/structured_history.txt",
    ]
    missing = [path for path in required if not (ROOT / path).exists()]
    assert not missing, missing


def test_reports_use_honest_language():
    readme = (ROOT / "README.md").read_text()
    report = (ROOT / "FOLLOWUP_REPORT.md").read_text()
    for text in [readme, report]:
        assert "F2P" in text
        assert "limitations" in text.lower() or "limitation" in text.lower()
        assert "does not" in text.lower() or "zero" in text.lower()


def test_reviewer_path_names_the_real_entry_points_and_metric_boundary():
    readme = (ROOT / "README.md").read_text()
    code_map = ROOT / "docs/code-map.md"
    assert code_map.is_file()
    code_map_text = code_map.read_text()

    for phrase in [
        "## Quickstart",
        "python scripts/verify_core_results.py",
        "replay --config configs/experiment4.json",
        "scripts/render_experiment2_prompt.py",
        "--run-label",
        "do not call the model",
        "rule-based",
        "0/10",
        "1/10",
        "6/10",
        "## Limitations",
    ]:
        assert phrase in readme

    for phrase in [
        "scripts/run_experiment2.py",
        "base_instructions()",
        "prompt_for()",
        "STRUCTURED_APPLICABILITY_AWARE",
        "src/history_guided_bug_discovery/application/prompts.py",
        "scripts/evaluate_experiment2.py",
        "scripts/verify_core_results.py",
    ]:
        assert phrase in code_map_text
