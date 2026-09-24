"""Materialize immutable Experiment 4 evidence snapshots from authoritative CSVs."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from history_guided_bug_discovery.application.evidence_bundle import write_evidence_bundle
from history_guided_bug_discovery.domain.enums import Arm


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "artifacts" / "experiment4" / "iteration3"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    for arm, filename in (
        (Arm.STRICT_PLANNER, "experiment4_iteration3_raw.csv"),
        (Arm.BUDGET_MATCHED_DIRECT, "experiment4_iteration3_raw_budgeted.csv"),
    ):
        source = ROOT / "results" / filename
        with source.open(newline="", encoding="utf-8") as handle:
            rows = [row for row in csv.DictReader(handle) if row.get("arm") == arm.value]
        path = write_evidence_bundle(
            ARTIFACT_ROOT,
            arm,
            rows,
            f"results/{filename}",
            sha256(source),
            "benchmark_f2p_v1",
            {"kind": "deterministic_snapshot", "source_commit": "30015986aa134499ede63da348d9dce8aa5da34f"},
        )
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
