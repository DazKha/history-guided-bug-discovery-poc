from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from ..config.models import RunConfig
from ..domain.enums import Arm
from ..reporting.aggregate import AggregateSummary, aggregate_rows


class ReplayPipeline:
    """Offline replay over preserved Experiment 4 machine-readable rows."""

    def replay(self, config: RunConfig, artifacts: str | Path, arm: Arm = Arm.STRICT_PLANNER) -> AggregateSummary:
        artifact_dir = Path(artifacts).resolve()
        if not artifact_dir.exists():
            raise FileNotFoundError(f"artifact directory does not exist: {artifact_dir}")
        root = artifact_dir.parents[2] if len(artifact_dir.parents) > 2 else Path.cwd()
        filename = "experiment4_iteration3_raw_budgeted.csv" if arm is Arm.BUDGET_MATCHED_DIRECT else "experiment4_iteration3_raw.csv"
        source = root / "results" / filename
        if not source.exists():
            raise FileNotFoundError(f"preserved replay CSV does not exist: {source}")
        with source.open(newline="", encoding="utf-8") as handle:
            rows = [row for row in csv.DictReader(handle) if row.get("arm") == arm.value]
        if not rows:
            raise ValueError(f"no replay rows for arm {arm.value}")
        return aggregate_rows(rows, arm)
