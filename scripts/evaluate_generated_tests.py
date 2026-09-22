from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIELDS = [
    "target_id", "condition", "condition_name", "attempt", "status", "test_path", "buggy_exit", "fixed_exit",
    "buggy_class", "fixed_class", "outcome", "meaningful_buggy_failure", "oracle_support", "hypothesis_claim",
    "repair_attempts", "llm_requests", "prompt_tokens", "completion_tokens", "latency_seconds", "buggy_log", "fixed_log",
]


def classify_output(exit_code: int, output: str) -> str:
    lower = output.lower()
    mechanical_markers = ["modulenotfounderror", "importerror", "syntaxerror", "filenotfounderror", "timeouterror", "no such file or directory", "error during collection"]
    if any(marker in lower for marker in mechanical_markers):
        return "MECHANICAL_FAILURE"
    if exit_code == 0:
        return "PASS"
    if "assert false" in lower:
        return "MECHANICAL_FAILURE"
    if "assertionerror" in lower or "assert " in lower or "pytest.fail" in lower:
        return "FAIL"
    return "MECHANICAL_FAILURE"


def classify_pair(buggy_exit: int, buggy_output: str, fixed_exit: int, fixed_output: str, hypothesis: str) -> str:
    buggy = classify_output(buggy_exit, buggy_output)
    fixed = classify_output(fixed_exit, fixed_output)
    if buggy == "MECHANICAL_FAILURE" or fixed == "MECHANICAL_FAILURE":
        return "MECHANICAL_FAILURE"
    return {("FAIL", "PASS"): "F2P", ("PASS", "PASS"): "P2P", ("FAIL", "FAIL"): "F2F", ("PASS", "FAIL"): "P2F"}[(buggy, fixed)]


def run_test(repo: Path, test_source: Path, log_path: Path) -> tuple[int, str]:
    test_name = f"_generated_eval_{test_source.stem}.py"
    injected = repo / test_name
    shutil.copyfile(test_source, injected)
    python = repo / "env39" / "bin" / "python"
    if not python.exists():
        python = Path("python3")
    env = os.environ.copy()
    env.update({"LC_ALL": "C", "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0", "PYTHONPATH": str(repo)})
    try:
        completed = subprocess.run([str(python), "-m", "pytest", "-q", test_name], cwd=repo, env=env, capture_output=True, text=True, timeout=90)
        output = (completed.stdout or "") + (completed.stderr or "")
        output = "\n".join(line.rstrip() for line in output.splitlines()) + "\n"
        log_path.write_text(output)
        return completed.returncode, output
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "") + (exc.stderr or "") + "\nTIMEOUT\n"
        output = "\n".join(line.rstrip() for line in output.splitlines()) + "\n"
        log_path.write_text(output)
        return 124, output
    finally:
        injected.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "data" / "case_manifest.json")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    target = manifest["target"]
    artifacts = sorted((ROOT / "artifacts" / "llm" / target["target_id"].replace(":", "_")).glob("*.json"))
    log_root = ROOT / "artifacts" / "execution_logs" / target["target_id"].replace(":", "_")
    log_root.mkdir(parents=True, exist_ok=True)
    rows = []
    for artifact in artifacts:
        record = json.loads(artifact.read_text())
        row = {field: "" for field in FIELDS}
        row.update({k: record.get(k, "") for k in ["target_id", "condition", "condition_name", "attempt", "status", "test_path", "repair_attempts"]})
        llm = record.get("llm", {})
        usage = llm.get("usage", {})
        row.update({"llm_requests": llm.get("request_count", 0), "prompt_tokens": usage.get("prompt_tokens", 0), "completion_tokens": usage.get("completion_tokens", 0), "latency_seconds": llm.get("latency_seconds", 0)})
        hypothesis = (record.get("hypothesis") or {}).get("claim", "")
        row["hypothesis_claim"] = hypothesis
        row["oracle_support"] = (record.get("hypothesis") or {}).get("oracle_evidence", "")
        if record.get("status") != "HYPOTHESIS" or not record.get("test_path"):
            row["outcome"] = record.get("status", "MECHANICAL_FAILURE")
            rows.append(row)
            continue
        base = f"{record['condition']}_attempt_{record['attempt']}"
        test_path = ROOT / record["test_path"]
        buggy_exit, buggy_output = run_test(ROOT / target["buggy_repo"], test_path, log_root / f"{base}_buggy.log")
        fixed_exit, fixed_output = run_test(ROOT / target["fixed_repo"], test_path, log_root / f"{base}_fixed.log")
        row.update({"buggy_exit": buggy_exit, "fixed_exit": fixed_exit, "buggy_class": classify_output(buggy_exit, buggy_output), "fixed_class": classify_output(fixed_exit, fixed_output), "outcome": classify_pair(buggy_exit, buggy_output, fixed_exit, fixed_output, hypothesis), "meaningful_buggy_failure": classify_output(buggy_exit, buggy_output) == "FAIL", "buggy_log": str((log_root / f"{base}_buggy.log").relative_to(ROOT)), "fixed_log": str((log_root / f"{base}_fixed.log").relative_to(ROOT))})
        rows.append(row)

    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)
    with (results_dir / "results.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    summary = []
    for condition in sorted({row["condition"] for row in rows}):
        subset = [row for row in rows if row["condition"] == condition]
        counts = {outcome: sum(row["outcome"] == outcome for row in subset) for outcome in ["F2P", "P2P", "F2F", "P2F", "MECHANICAL_FAILURE", "NO_SUPPORTED_HYPOTHESIS"]}
        summary.append({"condition": condition, "condition_name": subset[0]["condition_name"], "attempts": len(subset), **counts, "tests_generated": sum(bool(row["test_path"]) for row in subset), "meaningful_buggy_failures": sum(bool(row["meaningful_buggy_failure"]) for row in subset)})
    with (results_dir / "summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0].keys()) if summary else ["condition"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(summary)
    print(json.dumps({"rows": len(rows), "summary": summary}))


if __name__ == "__main__":
    main()
