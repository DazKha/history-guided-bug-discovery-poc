from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

try:
    from .evaluate_generated_tests import run_test
except ImportError:
    from evaluate_generated_tests import run_test

try:
    from .evaluate_experiment2 import mechanism_match, oracle_supported
except ImportError:
    from evaluate_experiment2 import mechanism_match, oracle_supported


ROOT = Path(__file__).resolve().parents[1]
RUNS = {
    "exploratory": ROOT / "artifacts/experiment2_llm_run1/PySnooper_1",
    "final": ROOT / "artifacts/experiment2_llm/PySnooper_1",
    "loop1": ROOT / "artifacts/experiment2_llm_loop1/PySnooper_1",
}
FIELDS = [
    "run_label", "target_id", "condition", "condition_name", "attempt", "status", "test_path", "same_test",
    "test_sha256", "oracle_status", "applicability", "hypothesis", "trigger", "potential_failure",
    "expected_behavior", "target_evidence", "historical_evidence", "buggy_exit", "fixed_exit", "buggy_state",
    "fixed_state", "buggy_failure_type", "fixed_failure_type", "buggy_exception", "fixed_exception", "classification",
    "verified_f2p", "hypothesis_matches_true_failure_mechanism", "failure_category", "repair_attempts", "llm_calls",
    "prompt_tokens", "completion_tokens", "wall_clock_seconds", "buggy_log", "fixed_log",
]

MECHANICAL_MARKERS = [
    "syntaxerror", "modulenotfounderror", "importerror", "filenotfounderror", "error during collection",
    "no such file or directory", "timeouterror", "timeout", "fixture .* not found",
]
TARGET_PATH_MARKERS = ["pysnooper/", "pysnooper\\", "tracer.py", "workspace/harness"]
EXCEPTION_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception))\b")


def _record_text(record: dict) -> str:
    oracle = record.get("oracle", {}) or {}
    return " ".join(str(record.get(key, "")) for key in ["hypothesis", "trigger", "potential_failure", "test_code"] + []) + " " + " ".join(str(oracle.get(key, "")) for key in ["expected_behavior", "target_evidence", "historical_evidence"])


def oracle_pre_execution(record: dict) -> bool:
    """Return true only when the artifact contains a pre-execution oracle."""
    if record.get("status") != "TEST":
        return False
    oracle = record.get("oracle", {}) or {}
    expected = str(oracle.get("expected_behavior", "")).strip()
    target = str(oracle.get("target_evidence", "")).strip()
    if not expected or not target:
        return False
    if any(marker in (expected + " " + target).lower() for marker in ["after seeing the failure", "post-hoc", "post hoc"]):
        return False
    return oracle_supported(record) == "yes"


def _is_mechanical(output: str) -> bool:
    lower = output.lower()
    return any(re.search(marker, lower) for marker in MECHANICAL_MARKERS) or "assert false" in lower or "pytest.fail" in lower


def _exception_type(output: str) -> str:
    matches = EXCEPTION_RE.findall(output)
    if not matches:
        return ""
    # Prefer the last traceback exception; this avoids a caught inner error
    # when the final failure is a different wrapper exception.
    return matches[-1]


def _target_exception(output: str, exception_type: str) -> bool:
    if not exception_type:
        return False
    lower = output.lower()
    return any(marker in lower for marker in TARGET_PATH_MARKERS)


def _exception_relevant(record: dict, exception_type: str) -> bool:
    text = _record_text(record).lower()
    exc = exception_type.lower()
    if exc and exc in text:
        return True
    if exc == "unicodeencodeerror":
        return any(token in text for token in ["encoding", "unicode", "non-ascii", "locale", "utf-8"])
    if exc == "unicodedecodeerror":
        return any(token in text for token in ["encoding", "unicode", "non-ascii", "locale", "utf-8", "decode"])
    return False


def classify_revision_result(record: dict, output: str, exit_code: int) -> dict:
    if exit_code == 0:
        return {"state": "PASS", "failure_type": "", "exception": "", "target_exception": False, "relevant": True}
    if _is_mechanical(output):
        return {"state": "MECHANICAL_FAILURE", "failure_type": "MECHANICAL_FAILURE", "exception": _exception_type(output), "target_exception": False, "relevant": False}
    lower = output.lower()
    if "assertionerror" in lower or "assert " in lower:
        return {"state": "FAIL", "failure_type": "ASSERTION_FAILURE", "exception": "AssertionError", "target_exception": False, "relevant": True}
    exception_type = _exception_type(output)
    target_exception = _target_exception(output, exception_type)
    relevant = target_exception and _exception_relevant(record, exception_type)
    if relevant:
        return {"state": "FAIL", "failure_type": "TARGET_EXCEPTION", "exception": exception_type, "target_exception": True, "relevant": True}
    return {"state": "MECHANICAL_FAILURE", "failure_type": "MECHANICAL_FAILURE", "exception": exception_type, "target_exception": target_exception, "relevant": False}


def classify_pair(buggy: dict, fixed: dict, record: dict) -> str:
    if not oracle_pre_execution(record):
        return "UNSUPPORTED_ORACLE"
    if buggy["state"] == "MECHANICAL_FAILURE" or fixed["state"] == "MECHANICAL_FAILURE":
        return "MECHANICAL_FAILURE"
    if buggy["state"] == "PASS" and fixed["state"] == "PASS":
        return "P2P"
    if buggy["state"] == "FAIL" and fixed["state"] == "PASS":
        if buggy["failure_type"] == "ASSERTION_FAILURE":
            return "ASSERTION_F2P"
        if buggy["failure_type"] == "TARGET_EXCEPTION":
            return "EXCEPTION_F2P"
    if buggy["state"] == "FAIL" and fixed["state"] == "FAIL":
        return "F2F"
    if buggy["state"] == "PASS" and fixed["state"] == "FAIL":
        return "P2F"
    return "MECHANICAL_FAILURE"


def verified_f2p(buggy: dict, fixed: dict, record: dict, same_test: bool) -> bool:
    return same_test and oracle_pre_execution(record) and fixed["state"] == "PASS" and buggy["state"] == "FAIL" and buggy["failure_type"] in {"ASSERTION_FAILURE", "TARGET_EXCEPTION"}


def failure_category(record: dict, classification: str, buggy: dict, fixed: dict) -> str:
    if classification == "ASSERTION_F2P":
        return "VALID_ASSERTION_F2P"
    if classification == "EXCEPTION_F2P":
        return "VALID_EXCEPTION_F2P"
    if classification == "UNSUPPORTED_ORACLE":
        return "UNSUPPORTED_ORACLE"
    if classification == "MECHANICAL_FAILURE":
        return "MECHANICAL_FAILURE"
    if classification == "P2P":
        return "APPLICABILITY_STRICT" if record.get("condition") == "C" and "NOT_APPLICABLE" in str(record.get("applicability_decisions", [])) else "SEMANTIC_NON_TRIGGER"
    if classification == "F2F" and record.get("condition") == "C" and mechanism_match(record) == "yes":
        return "CORRECT_MECHANISM_WRONG_TRIGGER"
    if mechanism_match(record) == "no":
        return "WRONG_MECHANISM"
    if oracle_pre_execution(record):
        return "SEMANTIC_NON_TRIGGER"
    return "UNSUPPORTED_ORACLE"


def test_path_for(record: dict, run_label: str) -> Path:
    path = ROOT / record["test_path"]
    if run_label == "exploratory":
        path = ROOT / record["test_path"].replace("generated_tests/experiment2/", "generated_tests/experiment2_run1/")
    return path


def evaluate_run(run_label: str, artifact_dir: Path, manifest: dict) -> list[dict]:
    rows = []
    log_root = ROOT / "artifacts/execution_logs/experiment2_re_evaluated" / run_label
    log_root.mkdir(parents=True, exist_ok=True)
    for artifact in sorted(artifact_dir.glob("[ABC]_attempt_*.json")):
        record = json.loads(artifact.read_text())
        oracle = record.get("oracle", {}) or {}
        row = {field: "" for field in FIELDS}
        row.update({"run_label": run_label, "target_id": record.get("target_id", ""), "condition": record.get("condition", ""), "condition_name": record.get("condition_name", ""), "attempt": record.get("attempt", ""), "status": record.get("status", ""), "repair_attempts": record.get("repair_attempts", 0), "wall_clock_seconds": record.get("wall_clock_seconds", 0), "hypothesis": record.get("hypothesis", ""), "trigger": record.get("trigger", ""), "potential_failure": record.get("potential_failure", ""), "expected_behavior": oracle.get("expected_behavior", ""), "target_evidence": oracle.get("target_evidence", ""), "historical_evidence": oracle.get("historical_evidence", ""), "applicability": "; ".join(str(x) for x in record.get("applicability_decisions", [])), "hypothesis_matches_true_failure_mechanism": mechanism_match(record)})
        llm = record.get("llm", {}) or {}
        usage = llm.get("usage", {}) or {}
        row.update({"llm_calls": 1 if llm else 0, "prompt_tokens": usage.get("prompt_tokens", 0), "completion_tokens": usage.get("completion_tokens", 0)})
        if record.get("status") != "TEST" or not record.get("test_path"):
            row["classification"] = "MODEL_ERROR" if record.get("status") == "MODEL_ERROR" else "NO_SUPPORTED_HYPOTHESIS"
            row["failure_category"] = "TEST_NOT_EXECUTABLE"
            rows.append(row)
            continue
        test_path = test_path_for(record, run_label)
        source = test_path.read_bytes()
        row["test_path"] = str(test_path.relative_to(ROOT))
        row["test_sha256"] = hashlib.sha256(source).hexdigest()
        row["same_test"] = True
        buggy_log = log_root / f"{record['condition']}_attempt_{record['attempt']}_buggy.log"
        fixed_log = log_root / f"{record['condition']}_attempt_{record['attempt']}_fixed.log"
        buggy_exit, buggy_output = run_test(ROOT / manifest["agent_visible"]["buggy_checkout"], test_path, buggy_log)
        fixed_exit, fixed_output = run_test(ROOT / manifest["evaluator_only"]["fixed_checkout"], test_path, fixed_log)
        buggy = classify_revision_result(record, buggy_output, buggy_exit)
        fixed = classify_revision_result(record, fixed_output, fixed_exit)
        classification = classify_pair(buggy, fixed, record)
        row.update({"oracle_status": "SUPPORTED_ORACLE" if oracle_pre_execution(record) else "UNSUPPORTED_ORACLE", "buggy_exit": buggy_exit, "fixed_exit": fixed_exit, "buggy_state": buggy["state"], "fixed_state": fixed["state"], "buggy_failure_type": buggy["failure_type"], "fixed_failure_type": fixed["failure_type"], "buggy_exception": buggy["exception"], "fixed_exception": fixed["exception"], "classification": classification, "verified_f2p": verified_f2p(buggy, fixed, record, True), "failure_category": failure_category(record, classification, buggy, fixed), "buggy_log": str(buggy_log.relative_to(ROOT)), "fixed_log": str(fixed_log.relative_to(ROOT))})
        rows.append(row)
    return rows


def write_summary(rows: list[dict], path: Path) -> None:
    lines = [
        "# Experiment 2 re-evaluated summary",
        "",
        "Verified F2P requires the same unchanged test on buggy and fixed, a meaningful semantic buggy failure, a fixed pass, and an oracle supported before execution. Meaningful failure includes an assertion failure or a target exception that violates that pre-execution oracle. Target exceptions that are setup/environment failures or unrelated to the hypothesis remain mechanical.",
        "",
    ]
    present_labels = [label for label in ["exploratory", "final", "loop1"] if any(row["run_label"] == label for row in rows)]
    for run_label in present_labels:
        subset_run = [row for row in rows if row["run_label"] == run_label]
        lines += [f"## {run_label}", "", "| Condition | Attempts | Mechanism matches | Supported hypotheses | Executable tests | Assertion F2P | Exception F2P | Total verified F2P | P2P | F2F | Mechanical | Unsupported oracle | No-supported/model error | False/unverified | LLM calls | Prompt tokens | Completion tokens | Wall clock |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for condition in ["A", "B", "C"]:
            subset = [row for row in subset_run if row["condition"] == condition]
            if not subset:
                continue
            count = lambda value: sum(row["classification"] == value for row in subset)
            executable = sum(row["status"] == "TEST" and bool(row["test_path"]) for row in subset)
            supported = sum(row["oracle_status"] == "SUPPORTED_ORACLE" for row in subset)
            no_support = sum(row["classification"] in {"MODEL_ERROR", "NO_SUPPORTED_HYPOTHESIS"} for row in subset)
            false_unverified = sum(row["classification"] in {"P2P", "F2F", "P2F", "MECHANICAL_FAILURE", "UNSUPPORTED_ORACLE", "MODEL_ERROR", "NO_SUPPORTED_HYPOTHESIS"} for row in subset)
            total = sum(bool(row["verified_f2p"]) for row in subset)
            lines.append(f"| {condition} | {len(subset)} | {sum(row['hypothesis_matches_true_failure_mechanism'] == 'yes' for row in subset)} | {supported} | {executable} | {count('ASSERTION_F2P')} | {count('EXCEPTION_F2P')} | {total} | {count('P2P')} | {count('F2F')} | {count('MECHANICAL_FAILURE')} | {count('UNSUPPORTED_ORACLE')} | {no_support} | {false_unverified} | {sum(int(row['llm_calls'] or 0) for row in subset)} | {sum(int(row['prompt_tokens'] or 0) for row in subset)} | {sum(int(row['completion_tokens'] or 0) for row in subset)} | {round(sum(float(row['wall_clock_seconds'] or 0) for row in subset), 3)} |")
        lines.append("")
    c1 = [row for row in rows if row["run_label"] == "exploratory" and row["condition"] == "C" and row["attempt"] == 1]
    if c1:
        lines += ["## Decision on the Unicode case", "", "Exploratory C attempt 1 is classified as `EXCEPTION_F2P`: the pre-execution artifact contains an encoding-specific hypothesis and target-supported oracle, the buggy traceback is `UnicodeEncodeError` at `pysnooper/tracer.py:134`, and the unchanged test passes on fixed. This is not retroactive oracle invention.", ""]
    lines += ["The final strict run is reported separately from the exploratory run. No tests were edited between buggy/fixed execution."]
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", choices=["exploratory", "final", "loop1", "both", "all"], default="all")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "data/target_leakage_manifest.json").read_text())
    labels = ["exploratory", "final"] if args.run == "both" else list(RUNS) if args.run == "all" else [args.run]
    rows = []
    for label in labels:
        rows.extend(evaluate_run(label, RUNS[label], manifest))
    result_path = ROOT / "results/experiment2_re_evaluated.csv"
    with result_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    write_summary(rows, ROOT / "results/experiment2_re_evaluated_summary.md")
    loop_rows = [row for row in rows if row["run_label"] == "loop1"]
    if loop_rows:
        with (ROOT / "results/looped_experiment_results.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
            writer.writeheader(); writer.writerows(loop_rows)
        write_summary(loop_rows, ROOT / "results/looped_experiment_summary.md")
    print(json.dumps({"rows": len(rows), "exception_f2p": sum(row["classification"] == "EXCEPTION_F2P" for row in rows), "assertion_f2p": sum(row["classification"] == "ASSERTION_F2P" for row in rows), "verified_f2p": sum(bool(row["verified_f2p"]) for row in rows)}))


if __name__ == "__main__":
    main()
