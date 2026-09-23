from __future__ import annotations

"""Evaluate Experiment 5 without changing the existing evaluator semantics."""

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

try:
    from .experiment5_execution import run_test
except ImportError:
    from experiment5_execution import run_test


ROOT = Path(__file__).resolve().parents[1]
MECHANICAL_MARKERS = ["syntaxerror", "modulenotfounderror", "importerror", "filenotfounderror", "error during collection", "no such file or directory", "timeouterror", "timeout", "fixture .* not found"]
EXCEPTION_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception))\b")
END_FIELDS = ["attempt_id", "target_id", "condition", "condition_name", "attempt", "status", "test_path", "test_sha256", "test_runner", "same_test", "oracle_status", "hypothesis", "trigger", "potential_failure", "expected_behavior", "target_evidence", "historical_evidence", "mechanism_match", "buggy_exit", "fixed_exit", "buggy_state", "fixed_state", "buggy_failure_type", "fixed_failure_type", "buggy_exception", "fixed_exception", "classification", "verified_f2p", "failure_category", "activation", "llm_calls", "prompt_tokens", "completion_tokens", "wall_clock_seconds", "buggy_log", "fixed_log", "error"]
COND = {"A": "TARGET_ONLY", "B": "NAIVE_RAW_HISTORY", "C": "STRUCTURED_APPLICABILITY_AWARE"}


def usage(record: dict) -> tuple[int, int, int]:
    llm = record.get("llm") or {}
    u = llm.get("usage") or {}
    return (1 if llm else 0, int(u.get("prompt_tokens", 0) or 0), int(u.get("completion_tokens", 0) or 0))


def _text(record: dict) -> str:
    oracle = record.get("oracle") or {}
    return " ".join(str(record.get(k, "")) for k in ("hypothesis", "trigger", "potential_failure", "test_code")) + " " + " ".join(str(oracle.get(k, "")) for k in ("expected_behavior", "target_evidence", "historical_evidence"))


def mechanism_match(record: dict, truth: dict) -> str:
    """Evaluator-only semantic rubric for the selected Tornado mechanism."""
    text = _text(record).lower()
    receiver = ("set_nodelay" in text or "nodelay" in text) and any(t in text for t in ("websocket", "ws_connection", "connection", "socket"))
    lifecycle = any(t in text for t in ("open", "handler", "stream", "receiver", "lifecycle"))
    target = any(t in text for t in ("tornado", "websocket"))
    return "yes" if receiver and lifecycle and target else "no"


def oracle_pre_execution(record: dict) -> bool:
    if record.get("status") != "TEST":
        return False
    oracle = record.get("oracle") or {}
    expected = str(oracle.get("expected_behavior", "")).strip()
    target = str(oracle.get("target_evidence", "")).strip()
    if not expected or not target:
        return False
    if any(marker in (expected + " " + target).lower() for marker in ("after seeing the failure", "post-hoc", "post hoc")):
        return False
    return any(marker in target.lower() for marker in ("tornado", "websocket", "source", "ordinary", "test"))


def _is_mechanical(output: str) -> bool:
    lower = output.lower()
    return any(re.search(marker, lower) for marker in MECHANICAL_MARKERS) or "assert false" in lower or "pytest.fail" in lower


def _exception_type(output: str) -> str:
    matches = EXCEPTION_RE.findall(output)
    return matches[-1] if matches else ""


def _target_exception(output: str, repo: Path, exception_type: str) -> bool:
    if not exception_type:
        return False
    lower = output.lower()
    return any(marker in lower for marker in ("tornado/", "tornado\\", str(repo).lower(), "workspace/experiment5"))


def _exception_relevant(record: dict, exception_type: str) -> bool:
    text = _text(record).lower()
    exc = exception_type.lower()
    return bool(exc and (exc in text or any(token in text for token in ("nodelay", "websocket", "connection", "handler"))))


def classify_revision(record: dict, output: str, exit_code: int, repo: Path) -> dict:
    if exit_code == 0:
        return {"state": "PASS", "failure_type": "", "exception": "", "target_exception": False, "relevant": True}
    if _is_mechanical(output):
        return {"state": "MECHANICAL_FAILURE", "failure_type": "MECHANICAL_FAILURE", "exception": _exception_type(output), "target_exception": False, "relevant": False}
    lower = output.lower()
    if "assertionerror" in lower or "assert " in lower:
        return {"state": "FAIL", "failure_type": "ASSERTION_FAILURE", "exception": "AssertionError", "target_exception": False, "relevant": True}
    exception_type = _exception_type(output)
    target_exception = _target_exception(output, repo, exception_type)
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
        return "ASSERTION_F2P" if buggy["failure_type"] == "ASSERTION_FAILURE" else "EXCEPTION_F2P"
    if buggy["state"] == "FAIL" and fixed["state"] == "FAIL":
        return "F2F"
    if buggy["state"] == "PASS" and fixed["state"] == "FAIL":
        return "P2F"
    return "MECHANICAL_FAILURE"


def failure_category(record: dict, classification: str, mechanism: str, buggy: dict, fixed: dict) -> str:
    if classification in {"ASSERTION_F2P", "EXCEPTION_F2P"}:
        return "VALID_SEMANTIC_F2P"
    if classification == "UNSUPPORTED_ORACLE":
        return "ORACLE_UNSUPPORTED"
    if classification == "MECHANICAL_FAILURE":
        return "MECHANICAL_FAILURE"
    if classification == "P2P":
        return "TRIGGER_TOO_WEAK" if mechanism == "yes" else "SEMANTIC_NON_TRIGGER"
    if classification == "F2F":
        return "TRIGGER_WRONG_SHAPE" if mechanism == "yes" else "SEMANTIC_NON_TRIGGER"
    if mechanism == "no":
        return "MECHANISM_WRONG"
    return "SEMANTIC_NON_TRIGGER"


def evaluate_record(record: dict, manifest: dict, log_root: Path, label: str, slot: str = "") -> dict:
    truth = manifest["evaluator_only"]["ground_truth"]
    mechanism = mechanism_match(record, truth)
    oracle = record.get("oracle") or {}
    calls, prompt_tokens, completion_tokens = usage(record)
    row = {field: "" for field in END_FIELDS}
    row.update({"attempt_id": record.get("attempt_id", record.get("hypothesis_id", "")), "target_id": record.get("target_id", "tornado:1"), "condition": record.get("condition", record.get("arm", "")), "condition_name": record.get("condition_name", record.get("arm", "")), "attempt": record.get("attempt", record.get("hypothesis_id", "")), "status": record.get("status", ""), "test_path": record.get("test_path", ""), "test_sha256": record.get("test_sha256", ""), "same_test": "True" if record.get("test_path") else "", "oracle_status": "SUPPORTED_ORACLE" if oracle_pre_execution(record) else "UNSUPPORTED_ORACLE", "hypothesis": record.get("hypothesis", ""), "trigger": record.get("trigger", ""), "potential_failure": record.get("potential_failure", ""), "expected_behavior": oracle.get("expected_behavior", ""), "target_evidence": oracle.get("target_evidence", ""), "historical_evidence": oracle.get("historical_evidence", ""), "mechanism_match": mechanism, "llm_calls": calls, "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "wall_clock_seconds": record.get("wall_clock_seconds", ""), "error": record.get("error", "")})
    if slot:
        row["attempt_id"] = f"{row['attempt_id']}__slot_{slot}"
    if record.get("status") != "TEST" or not record.get("test_path"):
        row.update({"classification": record.get("status", "MODEL_OUTPUT_FAILURE"), "failure_category": "MODEL_OUTPUT_FAILURE", "activation": "NOT_ACTIVATED"})
        return row
    test_path = ROOT / record["test_path"]
    source = test_path.read_bytes()
    row["test_sha256"] = hashlib.sha256(source).hexdigest()
    base = re.sub(r"[^A-Za-z0-9_.-]+", "_", f"{label}_{row['attempt_id']}")
    buggy_repo = ROOT / manifest["agent_visible"]["buggy_checkout"]
    fixed_repo = ROOT / manifest["evaluator_only"]["fixed_checkout"]
    buggy_log, fixed_log = log_root / f"{base}_buggy.log", log_root / f"{base}_fixed.log"
    buggy_exit, buggy_output, buggy_runner = run_test(buggy_repo, test_path, buggy_log)
    fixed_exit, fixed_output, fixed_runner = run_test(fixed_repo, test_path, fixed_log)
    buggy = classify_revision(record, buggy_output, buggy_exit, buggy_repo)
    fixed = classify_revision(record, fixed_output, fixed_exit, fixed_repo)
    classification = classify_pair(buggy, fixed, record)
    row.update({"test_runner": f"buggy:{buggy_runner};fixed:{fixed_runner}", "buggy_exit": buggy_exit, "fixed_exit": fixed_exit, "buggy_state": buggy["state"], "fixed_state": fixed["state"], "buggy_failure_type": buggy["failure_type"], "fixed_failure_type": fixed["failure_type"], "buggy_exception": buggy["exception"], "fixed_exception": fixed["exception"], "classification": classification, "verified_f2p": "True" if classification in {"ASSERTION_F2P", "EXCEPTION_F2P"} else "False", "failure_category": failure_category(record, classification, mechanism, buggy, fixed), "activation": "ACTIVATED" if buggy["state"] == "FAIL" else "NOT_ACTIVATED", "buggy_log": str(buggy_log.relative_to(ROOT)), "fixed_log": str(fixed_log.relative_to(ROOT))})
    return row


def evaluate_end_to_end() -> list[dict]:
    manifest = json.loads((ROOT / "data/experiment5_target_manifest.json").read_text())
    root = ROOT / "artifacts/experiment5/end_to_end"
    logs = ROOT / "artifacts/execution_logs/experiment5/end_to_end"
    rows = []
    for condition in ("A", "B", "C"):
        for path in sorted((root / condition).glob("attempt_*.json")):
            rows.append(evaluate_record(json.loads(path.read_text()), manifest, logs / condition, f"E5A_{condition}"))
    return rows


def write_rows(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=END_FIELDS, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["end_to_end"], default="end_to_end")
    args = parser.parse_args()
    rows = evaluate_end_to_end()
    write_rows(rows, ROOT / "results/experiment5_end_to_end.csv")
    print(json.dumps({"mode": args.mode, "rows": len(rows), "f2p": sum(row.get("verified_f2p") == "True" for row in rows), "mechanism_matches": sum(row.get("mechanism_match") == "yes" for row in rows)}))


if __name__ == "__main__":
    main()
