from __future__ import annotations

"""Evaluator-only selection of the first eligible Experiment 5B hypotheses."""

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    rows = list(csv.DictReader((ROOT / "results/experiment5_end_to_end.csv").open()))
    selected = []
    for row in rows:
        if row.get("condition") != "C":
            continue
        if row.get("mechanism_match") != "yes" or row.get("oracle_status") != "SUPPORTED_ORACLE":
            continue
        artifact = ROOT / "artifacts/experiment5/end_to_end/C" / f"attempt_{int(row['attempt']):02d}.json"
        selected.append({"attempt_id": row["attempt_id"], "attempt": int(row["attempt"]), "artifact": str(artifact.relative_to(ROOT)), "hypothesis": json.loads(artifact.read_text()), "selection_basis": "first eligible C attempt in evaluator-only order"})
        if len(selected) == 5:
            break
    result = {
        "experiment": "experiment5_conditional",
        "target_id": "tornado:1",
        "eligible_count": len(selected),
        "requested_count": 5,
        "underpowered": len(selected) < 5,
        "selection_order": "C attempts ascending; mechanism match and supported oracle determined only by evaluator output",
        "selected": selected,
        "stop_reason": "fewer than five eligible frozen C hypotheses; no hypotheses were synthesized or topped up" if len(selected) < 5 else "five hypotheses selected",
    }
    path = ROOT / "data/experiment5_selected_hypotheses.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"eligible_count": len(selected), "underpowered": len(selected) < 5}))


if __name__ == "__main__":
    main()
