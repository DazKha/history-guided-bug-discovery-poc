from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

try:
    from .evaluate_experiment2 import mechanism_match, oracle_supported
    from .evaluate_generated_tests import run_test
    from .re_evaluate_experiment2 import classify_pair, classify_revision_result, failure_category, oracle_pre_execution, verified_f2p
except ImportError:
    from evaluate_experiment2 import mechanism_match, oracle_supported
    from evaluate_generated_tests import run_test
    from re_evaluate_experiment2 import classify_pair, classify_revision_result, failure_category, oracle_pre_execution, verified_f2p


ROOT = Path(__file__).resolve().parents[1]
FIELDS = [
    "run_label", "mode", "arm", "hypothesis_id", "trigger_id", "trigger_type", "test_id", "status", "test_status",
    "test_path", "test_sha256", "same_test", "hypothesis_sha256", "mechanism_match", "oracle_status",
    "buggy_exit", "fixed_exit", "buggy_state", "fixed_state", "buggy_failure_type", "fixed_failure_type",
    "buggy_exception", "fixed_exception", "classification", "verified_f2p", "failure_category", "activation",
    "repair_attempts", "llm_calls", "prompt_tokens", "completion_tokens", "wall_clock_seconds", "buggy_log", "fixed_log",
]


def evaluate_record(record: dict, manifest: dict, log_root: Path) -> dict:
    row = {field: "" for field in FIELDS}
    trigger = record.get("trigger_plan", {}) or {}
    row.update({
        "run_label": record.get("run_label", ""), "mode": record.get("mode", ""), "arm": record.get("arm", ""), "hypothesis_id": record.get("hypothesis_id", ""),
        "trigger_id": record.get("trigger_id", "planner" if record.get("status") == "TRIGGER_PLANNER_ERROR" else "direct"), "trigger_type": trigger.get("trigger_type", "PLANNER" if record.get("status") == "TRIGGER_PLANNER_ERROR" else "DIRECT"),
        "test_id": record.get("test_id", ""), "status": record.get("status", ""), "test_path": record.get("test_path", ""),
        "test_sha256": record.get("test_sha256", ""), "hypothesis_sha256": record.get("hypothesis_sha256", ""),
        "mechanism_match": mechanism_match(record), "oracle_status": "SUPPORTED_ORACLE" if oracle_pre_execution(record) else "UNSUPPORTED_ORACLE",
        "repair_attempts": record.get("repair_attempts", 0), "wall_clock_seconds": record.get("wall_clock_seconds", 0),
    })
    if record.get("status") != "TEST" or not record.get("test_path"):
        row["test_status"] = "MODEL_OUTPUT_FAILURE"
        row["classification"] = record.get("status", "MODEL_ERROR")
        row["failure_category"] = "MODEL_OUTPUT_FAILURE"
        return row
    test_path = ROOT / record["test_path"]
    source = test_path.read_bytes()
    row["test_sha256"] = hashlib.sha256(source).hexdigest()
    row["same_test"] = True
    base = f"{record.get('mode','mode')}_{record.get('arm','arm')}_{record.get('hypothesis_id','h')}_{record.get('trigger_id','direct')}"
    buggy_log = log_root / f"{base}_buggy.log"
    fixed_log = log_root / f"{base}_fixed.log"
    buggy_exit, buggy_output = run_test(ROOT / manifest["agent_visible"]["buggy_checkout"], test_path, buggy_log)
    fixed_exit, fixed_output = run_test(ROOT / manifest["evaluator_only"]["fixed_checkout"], test_path, fixed_log)
    buggy = classify_revision_result(record, buggy_output, buggy_exit)
    fixed = classify_revision_result(record, fixed_output, fixed_exit)
    classification = classify_pair(buggy, fixed, record)
    row.update({
        "test_status": "EXECUTABLE", "buggy_exit": buggy_exit, "fixed_exit": fixed_exit,
        "buggy_state": buggy["state"], "fixed_state": fixed["state"], "buggy_failure_type": buggy["failure_type"],
        "fixed_failure_type": fixed["failure_type"], "buggy_exception": buggy["exception"], "fixed_exception": fixed["exception"],
        "classification": classification, "verified_f2p": verified_f2p(buggy, fixed, record, True),
        "failure_category": failure_category(record, classification, buggy, fixed),
        "activation": "ACTIVATED" if buggy["state"] == "FAIL" else "NOT_ACTIVATED",
        "buggy_log": str(buggy_log.relative_to(ROOT)), "fixed_log": str(fixed_log.relative_to(ROOT)),
    })
    return row


def load_records(mode: str, arm: str, run_label: str = "") -> list[dict]:
    suffix = f"_{run_label}" if run_label else ""
    directory = ROOT / "artifacts/experiment3_llm" / f"{mode}{suffix}" / arm
    records = []
    for path in sorted(directory.glob("*.json")):
        record = json.loads(path.read_text())
        if "planner" in path.name and record.get("status") != "TRIGGER_PLANNER_ERROR":
            continue
        record.setdefault("run_label", run_label)
        records.append(record)
    return records


def load_hypothesis_rows(mode: str, run_label: str = "") -> list[dict]:
    suffix = f"_{run_label}" if run_label else ""
    directory = ROOT / "artifacts/experiment3_llm" / f"{mode}{suffix}" / "hypotheses"
    rows = []
    for path in sorted(directory.glob("*.json")):
        record = json.loads(path.read_text())
        if record.get("status") == "TEST":
            continue
        row = {field: "" for field in FIELDS}
        row.update({
            "run_label": run_label, "mode": mode, "arm": "HYPOTHESIS_STAGE",
            "hypothesis_id": record.get("hypothesis_id", path.stem), "status": record.get("status", "MODEL_ERROR"),
            "test_status": "MODEL_OUTPUT_FAILURE", "classification": record.get("status", "MODEL_ERROR"),
            "failure_category": "HYPOTHESIS_STAGE", "llm_calls": 1 if record.get("llm") else 0,
            "prompt_tokens": (record.get("llm", {}).get("usage", {}) or {}).get("prompt_tokens", 0),
            "completion_tokens": (record.get("llm", {}).get("usage", {}) or {}).get("completion_tokens", 0),
        })
        rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["natural", "conditional", "all"], default="all")
    parser.add_argument("--run-label", default="")
    parser.add_argument("--natural-run-label", default="")
    parser.add_argument("--conditional-run-label", default="")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "data/target_leakage_manifest.json").read_text())
    modes = ["natural", "conditional"] if args.mode == "all" else [args.mode]
    default_labels = [label for label in args.run_label.split(",") if label] if args.run_label else [""]
    rows = []
    log_root = ROOT / "artifacts/execution_logs/experiment3"
    log_root.mkdir(parents=True, exist_ok=True)
    for mode in modes:
        selected = args.natural_run_label if mode == "natural" else args.conditional_run_label
        run_labels = [label for label in selected.split(",") if label] if selected else default_labels
        for run_label in run_labels:
            (log_root / (run_label or "default")).mkdir(parents=True, exist_ok=True)
            rows.extend(load_hypothesis_rows(mode, run_label))
            for arm in ["C1", "C2"]:
                for record in load_records(mode, arm, run_label):
                    rows.append(evaluate_record(record, manifest, log_root / (run_label or "default")))
    out = ROOT / "results/experiment3_results.csv"
    with out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    print(json.dumps({"rows": len(rows), "verified_f2p": sum(bool(row["verified_f2p"]) for row in rows)}))


if __name__ == "__main__":
    main()
