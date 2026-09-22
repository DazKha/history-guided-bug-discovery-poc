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
