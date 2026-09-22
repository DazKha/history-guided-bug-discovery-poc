from __future__ import annotations

"""Prepare the retrospectively selected Experiment 2 transfer case.

This preparation script may read evaluator-only benchmark material.  The
generation runner is a separate script and reads only the files listed as
agent-visible in data/target_leakage_manifest.json.
"""

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUGGY = ROOT / "workspace/harness-pysnooper-buggy/PySnooper"
FIXED = ROOT / "workspace/harness-pysnooper-fixed/PySnooper"
TARGET_ID = "PySnooper:1"
SELECTED = ["cookiecutter:1", "PySnooper:3"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True)


def make_context() -> Path:
    out = ROOT / "data/experiment2_target_context/PySnooper-1.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    files = [
        "README.md",
        "setup.py",
        "pysnooper/tracer.py",
        "pysnooper/pycompat.py",
        "pysnooper/utils.py",
        "pysnooper/variables.py",
        "tests/test_pysnooper.py",
    ]
    parts = [
        "TARGET CONTEXT FOR GENERATION\n",
        "This is the buggy checkout only. The context contains ordinary source, docs, and ordinary tests.\n",
        "Execution environment visible to the tester: Python 3.9.18; LC_ALL=C; PYTHONUTF8=0; PYTHONCOERCECLOCALE=0; pytest.\n",
        "Do not use benchmark metadata, Git history, a fixed checkout, or a hidden regression test.\n",
        "The target issue, target fix, target regression test, and changed-file metadata are not included.\n",
    ]
    for rel in files:
        path = BUGGY / rel
        if not path.exists():
            continue
        parts.append(f"\n===== {rel} =====\n")
        parts.append(path.read_text(errors="replace"))
    out.write_text("".join(parts))
    return out


def make_history() -> tuple[Path, Path]:
    raw_all = json.loads((ROOT / "data/historical_raw.json").read_text())
    by_id = {row["history_id"]: row for row in raw_all}
    raw = []
    structured = []
    for history_id in SELECTED:
        row = by_id[history_id]
        raw.append({
            "history_id": history_id,
            "project": row["project"],
            "bug_report": row["bug_report"],
            "commit_subject": row["commit_subject"],
            "buggy_commit_id": row["buggy_commit_id"],
            "fixed_commit_id": row["fixed_commit_id"],
            "fix_diff": row["evidence"]["fix_diff"],
            "regression_test": row["evidence"]["regression_test"],
            "source_references": row["source_references"],
        })
        if history_id == "cookiecutter:1":
            structured.append({
                "history_id": history_id,
                "Context": "Cookiecutter reads a JSON context file through cookiecutter.generate.generate_context.",
                "Preconditions": "A context JSON file is UTF-8 encoded and contains a non-ASCII value.",
                "Trigger": "The context file is read on a runtime whose locale/default text encoding is not guaranteed to be UTF-8.",
                "Expected Invariant": "Valid UTF-8 context data must decode to the same Unicode values independently of the process locale.",
                "Observed Failure": "The historical regression added a non-ASCII JSON fixture; the buggy implicit open could use the platform default encoding.",
                "Failure Mechanism": "Implicit text I/O encoding is locale-dependent; the fix makes the read encoding explicitly UTF-8.",
                "Oracle": "generate_context returns the expected mapping containing the exact non-ASCII value.",
                "Oracle Provenance": "Historical regression assertion plus the explicit encoding fix; target truth must still be established from target-side evidence.",
                "Test Strategy": "Create a UTF-8 input containing a non-ASCII value, call the public context-loading API, and assert the returned value is preserved.",
                "Evidence References": row["source_references"] + ["evidence.fix_diff", "evidence.regression_test"],
                "Confidence": {"mechanism": 0.98, "trigger": 0.95, "invariant": 0.95, "transfer_to_target": 0.85},
            })
        else:
            structured.append({
                "history_id": history_id,
                "Context": "PySnooper writes trace output to a path supplied to the public snoop decorator.",
                "Preconditions": "The caller selects a filesystem path rather than a stream.",
                "Trigger": "The path-output branch performs the write using the wrong captured path variable.",
                "Expected Invariant": "Tracing to a requested path writes the trace to that path and preserves the decorated function result.",
                "Observed Failure": "The historical test exercises file output and the fix changes the opened path variable.",
                "Failure Mechanism": "A path/output variable mismatch in a file-output closure can send behavior to the wrong location; this is only partial evidence for the target encoding mechanism.",
                "Oracle": "The requested output path contains the expected trace after the decorated function runs.",
                "Oracle Provenance": "Historical regression assertion and fix diff; transfer compatibility with the target is weak because encoding is not established.",
                "Test Strategy": "Decorate a small function with a temporary output path, run it, and assert result plus trace content at that path.",
                "Evidence References": row["source_references"] + ["evidence.fix_diff", "evidence.regression_test"],
                "Confidence": {"mechanism": 0.92, "trigger": 0.90, "invariant": 0.90, "transfer_to_target": 0.45},
            })
    raw_path = ROOT / "data/experiment2_historical_raw.json"
    structured_path = ROOT / "data/experiment2_historical_structured.json"
    raw_path.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n")
    structured_path.write_text(json.dumps(structured, indent=2, ensure_ascii=False) + "\n")
    return raw_path, structured_path


def make_evaluator_truth() -> Path:
    fixed_diff = git(BUGGY, "diff", "e21a31162f4c54be693d8ca8260e42393b39abd3", "56f22f8ffe1c6b2be4d2cf3ad1987fdb66113da", "--", "pysnooper/tracer.py", "pysnooper/pycompat.py", "tests/test_chinese.py", "tests/utils.py")
    regression = (FIXED / "tests/test_chinese.py").read_text()
    truth = {
        "target_id": TARGET_ID,
        "buggy_revision": "e21a31162f4c54be693d8ca8260e42393b39abd3",
        "fixed_revision": "56f22f8ffe1c6b2be4d2cf3ad1987fdb66113da",
        "true_trigger": "Run a snooped function that produces non-ASCII text while the process uses the C locale with Python UTF-8 mode disabled.",
        "expected_invariant": "PySnooper should write valid UTF-8 trace output and decode Python source with non-ASCII content without depending on the locale default encoding.",
        "actual_failure": "The buggy revision uses implicit/default text encoding in FileWriter.write and source decoding; under the controlled C locale it raises UnicodeEncodeError while writing Chinese text.",
        "failure_mechanism": "Locale-dependent implicit text encoding in real file/source I/O; the fixed revision specifies UTF-8.",
        "oracle": "The generated trace file is readable as UTF-8 and contains the non-ASCII value; the function returns normally.",
        "relevant_code_area": ["pysnooper/tracer.py:76-95", "pysnooper/tracer.py:127-135"],
        "hidden_regression_relative_path": "tests/test_chinese.py",
        "hidden_regression_sha256": sha256(FIXED / "tests/test_chinese.py"),
        "fixed_diff": fixed_diff,
        "hidden_regression": regression,
    }
    out = ROOT / "data/evaluator_truth/experiment2_PySnooper-1.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(truth, indent=2, ensure_ascii=False) + "\n")
    return out


def make_candidates() -> Path:
    candidates = {
        "selection_policy": "Retrospective evaluator comparison by mechanism, trigger, invariant, and behavioral context; not lexical similarity.",
        "candidates": [
            {
                "rank": 1,
                "target_bug": TARGET_ID,
                "historical_bugs": ["cookiecutter:1"],
                "shared_mechanism": "Implicit locale-dependent text decoding replaced by explicit UTF-8.",
                "why_transfer_is_plausible": "Both involve real file I/O with non-ASCII data; the historical fix and regression directly expose the explicit-encoding invariant.",
                "setup_difficulty": "low; target harness already verified",
                "leakage_risks": ["Do not expose target Chinese regression, target diff, or target changed-file metadata to generation."],
            },
            {
                "rank": 2,
                "target_bug": TARGET_ID,
                "historical_bugs": ["cookiecutter:1", "PySnooper:3"],
                "shared_mechanism": "Primary explicit-encoding transfer plus a partial file-output-path analogue.",
                "why_transfer_is_plausible": "The first case provides the mechanism signal; the second is in the same target project and reinforces testing public path output while remaining a distractor/weak analogue.",
                "setup_difficulty": "low; target harness already verified",
                "leakage_risks": ["The PySnooper project identity is visible through ordinary source context; the target bug ID and hidden test remain evaluator-only."],
            },
            {
                "rank": 3,
                "target_bug": TARGET_ID,
                "historical_bugs": ["PySnooper:2", "PySnooper:3", "cookiecutter:1", "cookiecutter:2", "cookiecutter:3", "cookiecutter:4"],
                "shared_mechanism": "Mixed historical pool with one strong, one partial, and four unrelated cases.",
                "why_transfer_is_plausible": "Contains a transferable case but introduces substantial distraction and was the original Exp1 selection.",
                "setup_difficulty": "low",
                "leakage_risks": ["History dilution can be mistaken for lack of transfer."],
            },
        ],
        "chosen_candidate": {
            "rank": 2,
            "target_bug": TARGET_ID,
            "historical_bugs": SELECTED,
            "reason": "Smallest two-case subset satisfying the requested transfer-feasibility design: one strong mechanism match and one partial same-domain analogue, with exact equality of B/C history.",
        },
    }
    out = ROOT / "data/transfer_case_candidates.json"
    out.write_text(json.dumps(candidates, indent=2) + "\n")
    return out


def make_manifest(context: Path, raw: Path, structured: Path, truth: Path) -> None:
    manifest = {
        "experiment": "experiment2_transfer_feasibility",
        "target_id": TARGET_ID,
        "agent_visible": {
            "target_context": str(context.relative_to(ROOT)),
            "historical_raw": str(raw.relative_to(ROOT)),
            "historical_structured": str(structured.relative_to(ROOT)),
            "buggy_checkout": "workspace/harness-pysnooper-buggy/PySnooper",
            "ordinary_runtime": {"python": "3.9.18", "LC_ALL": "C", "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0"},
        },
        "evaluator_only": {
            "truth_file": str(truth.relative_to(ROOT)),
            "fixed_checkout": "workspace/harness-pysnooper-fixed/PySnooper",
            "target_issue_report": "vendor/BugsInPy/projects/PySnooper/bugs/1/bug.info",
            "target_fix_diff": "vendor/BugsInPy/projects/PySnooper/bugs/1/bug_patch.txt",
            "target_regression_test": "workspace/harness-pysnooper-fixed/PySnooper/tests/test_chinese.py",
            "changed_file_metadata": "fixed revision diff --name-only",
        },
        "selected_history_ids": SELECTED,
        "historical_selection_note": "Historical cases were retrospectively selected to test transfer feasibility; this experiment does not validate autonomous retrieval.",
        "fairness": {"attempts_per_condition": 5, "max_repairs": 1, "same_target_context": True, "same_model": True, "same_generation_budget": True, "same_execution_environment": True},
        "model": {"name": "deepseek-flash", "endpoint": "https://api.deepseek.com/chat/completions", "temperature": 0.2, "max_tokens": 2200, "thinking": "disabled"},
    }
    (ROOT / "data/target_leakage_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def main() -> None:
    context = make_context()
    raw, structured = make_history()
    truth = make_evaluator_truth()
    make_candidates()
    make_manifest(context, raw, structured, truth)
    print(json.dumps({"context": str(context), "raw": str(raw), "structured": str(structured), "truth": str(truth)}))


if __name__ == "__main__":
    main()
