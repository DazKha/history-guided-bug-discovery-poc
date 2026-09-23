from __future__ import annotations

"""Materialize the Experiment 5B stop condition without top-up generation."""

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["hypothesis_id", "arm", "candidate_slot", "status", "classification", "verified_f2p", "failure_category", "planner_calls", "test_generation_calls", "test_path", "test_sha256", "buggy_log", "fixed_log", "error"]


def main() -> None:
    selection = json.loads((ROOT / "data/experiment5_selected_hypotheses.json").read_text())
    if selection["eligible_count"] < 5:
        rows: list[dict[str, str]] = []
        with (ROOT / "results/experiment5_conditional.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        (ROOT / "artifacts/experiment5/conditional_run_status.json").write_text(json.dumps({"experiment": "experiment5_conditional", "status": "UNDERPOWERED_STOP", "eligible_count": selection["eligible_count"], "planner_calls": 0, "test_generation_calls": 0, "reason": selection["stop_reason"]}, indent=2) + "\n")
        print(json.dumps({"status": "UNDERPOWERED_STOP", "eligible_count": selection["eligible_count"], "planner_calls": 0}))
        return
    raise RuntimeError("Conditional implementation is intentionally not invoked by this underpowered replication.")


if __name__ == "__main__":
    main()
