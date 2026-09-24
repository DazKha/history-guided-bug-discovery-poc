"""Verify the frozen Experiment 4 hashes, evidence bundles, metrics, and reports."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from history_guided_bug_discovery.application.replay_pipeline import ReplayPipeline
from history_guided_bug_discovery.config.loader import load_config
from history_guided_bug_discovery.domain.enums import Arm
from history_guided_bug_discovery.reporting.aggregate import validate_report_files
from history_guided_bug_discovery.reporting.csv_report import write_csv
from history_guided_bug_discovery.reporting.markdown import write_markdown


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_HASHES = {
    "results/experiment4_iteration3_raw.csv": "6b5a316a26e044f640c76913b1dd78a2cd1a2b7092d97cc90ad198183c21efd8",
    "results/experiment4_iteration3_raw_budgeted.csv": "6a21ff378b7ddcad3bbaccbce3bbda835520444a870b3cecc219356bae26959b",
}
EXPECTED = {
    "C2": {"candidate_slots": 15, "generated_test_artifacts": 13, "f2p": 5, "f2p_hypotheses": 4, "p2p": 3, "mechanical_failures": 5, "model_output_failures": 2, "f2f": 0, "llm_calls": 21, "total_tokens": 326930},
    "C1_BUDGETED": {"candidate_slots": 15, "generated_test_artifacts": 13, "f2p": 6, "f2p_hypotheses": 3, "p2p": 5, "f2f": 2, "model_output_failures": 2, "llm_calls": 15, "total_tokens": 15801},
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    for relative, expected in EXPECTED_HASHES.items():
        path = ROOT / relative
        if not path.is_file():
            raise SystemExit(f"required baseline is missing: {relative}")
        actual = sha256(path)
        if actual != expected:
            raise SystemExit(f"baseline hash mismatch for {relative}: {actual} != {expected}")
    required = [
        ROOT / "README.md", ROOT / "research_log.md", ROOT / "data/case_manifest.json",
        ROOT / "data/historical_raw.json", ROOT / "data/historical_structured.json",
        ROOT / "results/results.csv", ROOT / "results/summary.csv", ROOT / "results/failure_analysis.md",
        ROOT / "FOLLOWUP_REPORT.md",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise SystemExit("required artifact(s) missing: " + ", ".join(missing))
    config = load_config(ROOT / "configs/experiment4.json")
    replay = ReplayPipeline()
    for arm in (Arm.STRICT_PLANNER, Arm.BUDGET_MATCHED_DIRECT):
        summary = replay.replay(config, ROOT / "artifacts/experiment4/iteration3", arm)
        for key, expected in EXPECTED[arm.value].items():
            if getattr(summary, key) != expected:
                raise SystemExit(f"{arm.value} metric mismatch for {key}: {getattr(summary, key)} != {expected}")
        with tempfile.TemporaryDirectory(prefix="experiment4-report-") as directory:
            output = Path(directory)
            json_path = output / "summary.json"
            csv_path = output / "summary.csv"
            markdown_path = output / "summary.md"
            json_path.write_text(json.dumps(summary.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            write_csv(summary, csv_path)
            write_markdown(summary, markdown_path)
            validate_report_files(json_path, csv_path, markdown_path)
    print("Experiment 4 evidence, hashes, metrics, and report consistency verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
