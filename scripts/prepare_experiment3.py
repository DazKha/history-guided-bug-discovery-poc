from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = {
    "exploratory": ROOT / "artifacts/experiment2_llm_run1/PySnooper_1",
    "final": ROOT / "artifacts/experiment2_llm/PySnooper_1",
    "loop1": ROOT / "artifacts/experiment2_llm_loop1/PySnooper_1",
    "replication2b": ROOT / "artifacts/experiment2_llm_replication2b/PySnooper_1",
    "replication2c": ROOT / "artifacts/experiment2_llm_replication2c/PySnooper_1",
}


def prepare(limit: int = 5) -> list[dict]:
    evaluated = list(__import__("csv").DictReader((ROOT / "results/experiment2_re_evaluated.csv").open()))
    selected = [
        row for row in evaluated
        if row.get("condition") == "C" and row.get("hypothesis_matches_true_failure_mechanism") == "yes"
    ][:limit]
    records = []
    visible = [
        "data/experiment2_target_context/PySnooper-1.txt",
        "data/experiment2_historical_structured.json",
    ]
    for index, row in enumerate(selected, 1):
        source = SOURCE_DIRS[row["run_label"]] / f"C_attempt_{int(row['attempt'])}.json"
        raw = json.loads(source.read_text())
        record = {
            "experiment": "experiment3",
            "mode": "conditional",
            "attempt": index,
            "hypothesis_id": f"conditional-h{index:02d}",
            "status": raw.get("status", "TEST"),
            "hypothesis": raw.get("hypothesis", ""),
            "trigger": raw.get("trigger", ""),
            "potential_failure": raw.get("potential_failure", ""),
            "oracle": raw.get("oracle", {}),
            "applicability_decisions": raw.get("applicability_decisions", []),
            "hypothesis_frozen": True,
            "generation_visible_files": visible,
            "source_artifact": str(source.relative_to(ROOT)),
        }
        record["hypothesis_sha256"] = hashlib.sha256(json.dumps({key: record.get(key) for key in ("hypothesis", "trigger", "potential_failure", "oracle")}, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
        records.append(record)
    out = ROOT / "data/experiment3_conditional_hypotheses.json"
    out.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    records = prepare(args.limit)
    print(json.dumps({"records": len(records), "output": "data/experiment3_conditional_hypotheses.json"}))


if __name__ == "__main__":
    main()

