from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from .evaluate_experiment2 import mechanism_match
    from .evaluate_generated_tests import run_test
    from .re_evaluate_experiment2 import classify_pair, classify_revision_result, failure_category, oracle_pre_execution, verified_f2p
except ImportError:
    from evaluate_experiment2 import mechanism_match
    from evaluate_generated_tests import run_test
    from re_evaluate_experiment2 import classify_pair, classify_revision_result, failure_category, oracle_pre_execution, verified_f2p


ROOT = Path(__file__).resolve().parents[1]
FIELDS = [
    "iteration", "mode", "arm", "stage", "hypothesis_id", "trigger_id", "trigger_type", "test_id", "status", "test_status",
    "test_path", "test_sha256", "same_test", "hypothesis_sha256", "mechanism_match", "oracle_status", "buggy_exit", "fixed_exit",
    "buggy_state", "fixed_state", "buggy_failure_type", "fixed_failure_type", "buggy_exception", "fixed_exception", "classification",
    "verified_f2p", "failure_category", "activation", "planner_attempt_index", "planner_attempt_status", "repair_attempts", "llm_calls",
    "prompt_tokens", "completion_tokens", "wall_clock_seconds", "buggy_log", "fixed_log", "error",
]


def usage_totals(records: list[dict[str, Any]]) -> tuple[int, int]:
    prompt = completion = 0
    for record in records:
        usage = record.get("llm", {}).get("usage", {}) or {}
        prompt += int(usage.get("prompt_tokens", 0) or 0)
        completion += int(usage.get("completion_tokens", 0) or 0)
    return prompt, completion


def plan_error_category(error: str) -> str:
    text = error.lower()
    if "malformed json" in text or "response must contain" in text:
        return "MALFORMED_SCHEMA"
    if "missing required" in text:
        return "MISSING_REQUIRED_FIELD"
    if "unsupported action" in text:
        return "UNSUPPORTED_ACTION"
    if "invoke action" in text or "observe action" in text or "after invoke" in text:
        return "INCOMPLETE_STATE_TRANSITION"
    if "observable" in text and ("supported" in text or "required" in text):
        return "OBSERVABLE_UNAVAILABLE"
    if "assertion" in text:
        return "ASSERTION_MISALIGNED"
    if "leakage" in text:
        return "LEAKAGE_CONTROL"
    if "duplicate" in text:
        return "DUPLICATE_PLAN"
    return "PLAN_VALIDATION_OTHER"


def empty_row(record: dict[str, Any], stage: str) -> dict[str, Any]:
    row = {field: "" for field in FIELDS}
    row.update({
        "iteration": record.get("iteration", ""), "mode": record.get("mode", "conditional"), "arm": record.get("arm", ""),
        "stage": stage, "hypothesis_id": record.get("hypothesis_id", ""), "hypothesis_sha256": record.get("hypothesis_sha256", ""),
        "mechanism_match": mechanism_match(record), "oracle_status": "SUPPORTED_ORACLE" if oracle_pre_execution(record) else "UNSUPPORTED_ORACLE",
    })
    return row


def planner_rows(record: dict[str, Any]) -> list[dict[str, Any]]:
    attempts = record.get("planner_attempts", [])
    rows = []
    for attempt in attempts:
        row = empty_row(record, "PLANNER")
        status = attempt.get("status", "MODEL_ERROR")
        row.update({
            "trigger_id": "planner", "trigger_type": "PLAN", "status": status,
            "test_status": "NOT_EXECUTED", "planner_attempt_index": attempt.get("attempt", ""),
            "planner_attempt_status": status, "repair_attempts": attempt.get("attempt", 0),
            "failure_category": "VALID_PLAN" if status == "VALID" else plan_error_category(attempt.get("error", "")),
            "classification": "PLAN_VALID" if status == "VALID" else "PLAN_INVALID",
            "error": attempt.get("error", ""),
        })
        prompt, completion = usage_totals([attempt])
        row.update({"llm_calls": 1, "prompt_tokens": prompt, "completion_tokens": completion, "wall_clock_seconds": attempt.get("wall_clock_seconds", "")})
        rows.append(row)
    return rows


def evaluate_test(record: dict[str, Any], manifest: dict[str, Any], log_root: Path) -> dict[str, Any]:
    row = empty_row(record, "TEST")
    plan = record.get("trigger_plan", {}) or {}
    row.update({
        "trigger_id": record.get("trigger_id", ""), "trigger_type": record.get("trigger_type", "PLAN"), "test_id": record.get("test_id", ""),
        "status": record.get("status", ""), "test_path": record.get("test_path", ""), "test_sha256": record.get("test_sha256", ""),
        "repair_attempts": record.get("repair_attempts", 0), "error": record.get("error", ""),
    })
    prompt, completion = usage_totals([record])
    row.update({"llm_calls": 1 if record.get("llm") else 0, "prompt_tokens": prompt, "completion_tokens": completion, "wall_clock_seconds": record.get("wall_clock_seconds", "")})
    if record.get("status") != "TEST" or not record.get("test_path"):
        row.update({"test_status": "MODEL_OUTPUT_FAILURE", "classification": record.get("status", "MODEL_ERROR"), "failure_category": "MODEL_OUTPUT_FAILURE"})
        return row
    test_path = ROOT / record["test_path"]
    source = test_path.read_bytes()
    row.update({"test_status": "EXECUTABLE", "test_sha256": hashlib.sha256(source).hexdigest(), "same_test": True})
    base = f"iteration{record.get('iteration','x')}_{record.get('arm','x')}_{record.get('hypothesis_id','h')}_{record.get('trigger_id','t')}"
    buggy_log = log_root / f"{base}_buggy.log"
    fixed_log = log_root / f"{base}_fixed.log"
    buggy_exit, buggy_output = run_test(ROOT / manifest["agent_visible"]["buggy_checkout"], test_path, buggy_log)
    fixed_exit, fixed_output = run_test(ROOT / manifest["evaluator_only"]["fixed_checkout"], test_path, fixed_log)
    buggy = classify_revision_result(record, buggy_output, buggy_exit)
    fixed = classify_revision_result(record, fixed_output, fixed_exit)
    classification = classify_pair(buggy, fixed, record)
    row.update({
        "buggy_exit": buggy_exit, "fixed_exit": fixed_exit, "buggy_state": buggy["state"], "fixed_state": fixed["state"],
        "buggy_failure_type": buggy["failure_type"], "fixed_failure_type": fixed["failure_type"], "buggy_exception": buggy["exception"],
        "fixed_exception": fixed["exception"], "classification": classification, "verified_f2p": verified_f2p(buggy, fixed, record, True),
        "failure_category": failure_category(record, classification, buggy, fixed), "activation": "ACTIVATED" if buggy["state"] == "FAIL" else "NOT_ACTIVATED",
        "buggy_log": str(buggy_log.relative_to(ROOT)), "fixed_log": str(fixed_log.relative_to(ROOT)),
    })
    return row


def load_records(root: Path) -> list[dict[str, Any]]:
    records = []
    for arm in ("C1", "C1_BUDGETED", "C2"):
        for path in sorted((root / arm).glob("*.json")):
            record = json.loads(path.read_text())
            if arm == "C2" and path.name.endswith("__planner.json"):
                records.extend(planner_rows(record))
                continue
            records.append(record)
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iteration", type=int, choices=[1, 2, 3], required=True)
    parser.add_argument("--arms", default="C1,C2")
    parser.add_argument("--output-suffix", default="")
    args = parser.parse_args()
    root = ROOT / "artifacts/experiment4" / f"iteration{args.iteration}"
    manifest = json.loads((ROOT / "data/target_leakage_manifest.json").read_text())
    log_root = ROOT / "artifacts/execution_logs/experiment4" / f"iteration{args.iteration}"
    log_root.mkdir(parents=True, exist_ok=True)
    selected_arms = {arm.strip() for arm in args.arms.split(",") if arm.strip()}
    rows = []
    for record in load_records(root):
        if record.get("arm") not in selected_arms:
            continue
        if isinstance(record, dict) and record.get("stage") == "PLANNER":
            rows.append(record)
        else:
            rows.append(evaluate_test(record, manifest, log_root))
    out = ROOT / "results" / f"experiment4_iteration{args.iteration}_raw{args.output_suffix}.csv"
    with out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    print(json.dumps({"iteration": args.iteration, "rows": len(rows), "tests": sum(row.get("stage") == "TEST" for row in rows), "f2p": sum(row.get("verified_f2p") == "True" for row in rows)}))


if __name__ == "__main__":
    main()
