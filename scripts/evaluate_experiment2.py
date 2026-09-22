from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from evaluate_generated_tests import classify_output, run_test


ROOT = Path(__file__).resolve().parents[1]
OUTCOME_FIELDS = ["F2P", "P2P", "F2F", "P2F", "MECHANICAL_FAILURE"]
FIELDS = [
    "experiment", "target_id", "condition", "condition_name", "attempt", "status", "test_path",
    "applicability", "buggy_exit", "fixed_exit", "buggy_class", "fixed_class", "outcome",
    "meaningful_buggy_failure", "hypothesis_matches_true_failure_mechanism", "oracle_supported_by_target_evidence",
    "hypothesis", "trigger", "potential_failure", "expected_behavior", "target_evidence", "historical_evidence",
    "repair_attempts", "llm_requests", "prompt_tokens", "completion_tokens", "latency_seconds", "wall_clock_seconds",
    "buggy_log", "fixed_log", "failure_layer",
]


def pair_outcome(buggy_class: str, fixed_class: str) -> str:
    if "MECHANICAL_FAILURE" in {buggy_class, fixed_class}:
        return "MECHANICAL_FAILURE"
    return {("FAIL", "PASS"): "F2P", ("PASS", "PASS"): "P2P", ("FAIL", "FAIL"): "F2F", ("PASS", "FAIL"): "P2F"}[(buggy_class, fixed_class)]


def mechanism_match(record: dict) -> str:
    text = " ".join(str(record.get(k, "")) for k in ["hypothesis", "trigger", "potential_failure", "test_code"])
    text += " " + " ".join(str(record.get("oracle", {}).get(k, "")) for k in ["expected_behavior", "target_evidence", "historical_evidence"])
    lower = text.lower()
    encoding_signal = any(token in lower for token in ["utf-8", "utf8", "encoding", "unicode", "non-ascii", "non_ascii", "locale"])
    target_signal = any(token in lower for token in ["pysnooper", "snoop", "trace", "filewriter", "tracer.py", "output path"])
    return "yes" if encoding_signal and target_signal else "no"


def oracle_supported(record: dict) -> str:
    target = str(record.get("oracle", {}).get("target_evidence", "")).lower()
    if not target:
        return "no"
    target_markers = ["tracer.py", "filewriter", "pysnooper", "readme", "ordinary", "lc_all", "pythonutf8", "source", "test"]
    historical_only = target in {"historical evidence", "the historical regression", "historical test"}
    return "yes" if not historical_only and any(marker in target for marker in target_markers) else "no"


def failure_layer(record: dict, outcome: str) -> str:
    if record.get("status") == "NO_SUPPORTED_HYPOTHESIS":
        return "APPLICABILITY" if record.get("condition") == "C" else "HYPOTHESIS"
    if record.get("status") != "TEST":
        return "TEST_GENERATION"
    if outcome == "MECHANICAL_FAILURE":
        return "MECHANICAL_EXECUTION"
    if outcome == "F2P":
        return ""
    if record.get("condition") == "C" and record.get("applicability") in {"NOT_APPLICABLE", "WEAK"}:
        return "APPLICABILITY"
    if record.get("hypothesis_matches_true_failure_mechanism") == "no":
        return "HYPOTHESIS"
    if record.get("oracle_supported_by_target_evidence") == "no":
        return "ORACLE"
    return "SEMANTIC_NON_TRIGGER"


def summarize(rows: list[dict]) -> list[dict]:
    summary = []
    for condition in ["A", "B", "C"]:
        subset = [row for row in rows if row["condition"] == condition]
        counts = {name: sum(row["outcome"] == name for row in subset) for name in OUTCOME_FIELDS}
        summary.append({
            "condition": condition,
            "condition_name": subset[0]["condition_name"] if subset else "",
            "attempts": len(subset),
            "hypotheses_generated": sum(row["status"] == "TEST" for row in subset),
            "supported_hypotheses": sum(row["status"] == "TEST" and row["oracle_supported_by_target_evidence"] == "yes" for row in subset),
            "executable_tests": sum(bool(row["test_path"]) for row in subset),
            "meaningful_failures_on_buggy": sum(bool(row["meaningful_buggy_failure"]) for row in subset),
            "F2P": counts["F2P"], "F2F": counts["F2F"], "P2P": counts["P2P"], "P2F": counts["P2F"],
            "MECHANICAL_FAILURE": counts["MECHANICAL_FAILURE"],
            "NO_SUPPORTED_HYPOTHESIS": sum(row["status"] == "NO_SUPPORTED_HYPOTHESIS" for row in subset),
            "false_or_unverified_reports": sum(row["outcome"] in {"P2P", "F2F", "P2F", "MECHANICAL_FAILURE"} for row in subset),
            "mechanism_match_yes": sum(row["hypothesis_matches_true_failure_mechanism"] == "yes" for row in subset),
            "oracle_supported_yes": sum(row["oracle_supported_by_target_evidence"] == "yes" for row in subset),
            "repair_attempts": sum(int(row["repair_attempts"] or 0) for row in subset),
            # Each artifact corresponds to one bounded DeepSeek call. The row's
            # llm_requests value is the client's cumulative counter, so do not
            # mistake it for a per-condition count.
            "llm_calls": len(subset),
            "prompt_tokens": sum(int(row["prompt_tokens"] or 0) for row in subset),
            "completion_tokens": sum(int(row["completion_tokens"] or 0) for row in subset),
            "wall_clock_seconds": round(sum(float(row["wall_clock_seconds"] or 0) for row in subset), 3),
        })
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, default=ROOT / "artifacts/experiment2_llm/PySnooper_1")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "data/target_leakage_manifest.json").read_text())
    truth = json.loads((ROOT / manifest["evaluator_only"]["truth_file"]).read_text())
    # Truth is deliberately loaded only by this evaluator, never by run_experiment2.py.
    rows = []
    logs = ROOT / "artifacts/execution_logs/experiment2_PySnooper_1"
    logs.mkdir(parents=True, exist_ok=True)
    for artifact in sorted(args.artifact_dir.glob("[ABC]_attempt_*.json")):
        record = json.loads(artifact.read_text())
        oracle = record.get("oracle", {})
        row = {field: "" for field in FIELDS}
        row.update({k: record.get(k, "") for k in ["experiment", "target_id", "condition", "condition_name", "attempt", "status", "test_path", "repair_attempts", "wall_clock_seconds"]})
        row.update({"applicability": "; ".join(str(x) for x in record.get("applicability_decisions", []))})
        row.update({"hypothesis": record.get("hypothesis", ""), "trigger": record.get("trigger", ""), "potential_failure": record.get("potential_failure", ""), "expected_behavior": oracle.get("expected_behavior", ""), "target_evidence": oracle.get("target_evidence", ""), "historical_evidence": oracle.get("historical_evidence", "")})
        row["hypothesis_matches_true_failure_mechanism"] = mechanism_match(record)
        row["oracle_supported_by_target_evidence"] = oracle_supported(record)
        llm = record.get("llm", {})
        usage = llm.get("usage", {}) or {}
        row.update({"llm_requests": llm.get("request_count", 0), "prompt_tokens": usage.get("prompt_tokens", 0), "completion_tokens": usage.get("completion_tokens", 0), "latency_seconds": llm.get("latency_seconds", 0)})
        if record.get("status") != "TEST" or not record.get("test_path"):
            row["outcome"] = record.get("status", "MODEL_ERROR")
            row["failure_layer"] = failure_layer(row, row["outcome"])
            row["meaningful_buggy_failure"] = False
            rows.append(row)
            continue
        test_path = ROOT / record["test_path"]
        base = f"{record['condition']}_attempt_{record['attempt']}"
        buggy_log = logs / f"{base}_buggy.log"
        fixed_log = logs / f"{base}_fixed.log"
        buggy_exit, buggy_output = run_test(ROOT / manifest["agent_visible"]["buggy_checkout"], test_path, buggy_log)
        fixed_exit, fixed_output = run_test(ROOT / manifest["evaluator_only"]["fixed_checkout"], test_path, fixed_log)
        row.update({"buggy_exit": buggy_exit, "fixed_exit": fixed_exit, "buggy_class": classify_output(buggy_exit, buggy_output), "fixed_class": classify_output(fixed_exit, fixed_output)})
        row["outcome"] = pair_outcome(row["buggy_class"], row["fixed_class"])
        row["meaningful_buggy_failure"] = row["buggy_class"] == "FAIL"
        row["buggy_log"] = str(buggy_log.relative_to(ROOT))
        row["fixed_log"] = str(fixed_log.relative_to(ROOT))
        row["failure_layer"] = failure_layer(row, row["outcome"])
        rows.append(row)
    result_path = ROOT / "results/experiment2_results.csv"
    with result_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    summary = summarize(rows)
    summary_path = ROOT / "results/experiment2_summary.csv"
    with summary_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0].keys()), lineterminator="\n")
        writer.writeheader(); writer.writerows(summary)
    print(json.dumps({"rows": len(rows), "summary": summary, "truth_used_for_evaluation": truth["target_id"]}))


if __name__ == "__main__":
    main()
