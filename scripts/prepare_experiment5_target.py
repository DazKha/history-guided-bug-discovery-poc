from __future__ import annotations

"""Prepare the frozen second-target transfer case.

This evaluator-side preparation is intentionally separate from generation.  It
may read benchmark metadata and the fixed checkout, while generation scripts
read only the agent-visible paths recorded in the resulting manifest.
"""

import hashlib
import json
import shutil
from pathlib import Path

from prepare_data import build_target_context


ROOT = Path(__file__).resolve().parents[1]
SOURCE_BUGGY = ROOT / "workspace/experiment5_candidates/tornado-1-buggy"
SOURCE_FIXED = ROOT / "workspace/experiment5_candidates/tornado-1-fixed"
BUGGY = ROOT / "workspace/experiment5/tornado-buggy"
FIXED = ROOT / "workspace/experiment5/tornado-fixed"
TARGET_ID = "tornado:1"
ANALOGUES = ["PySnooper:3", "cookiecutter:1"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_checkout(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def make_context() -> Path:
    excluded = {
        "tornado/test/websocket_test.py",
        "bug.info",
        "bug_patch.txt",
        "run_test.sh",
        "setup.sh",
    }
    body = build_target_context(BUGGY, excluded)
    header = (
        "TARGET CONTEXT FOR EXPERIMENT 5 GENERATION\n"
        "This is the buggy Tornado checkout only. It contains bounded public source, documentation, and ordinary tests.\n"
        "Execution environment visible to the tester: Python 3.9.18; LC_ALL=C; PYTHONUTF8=0; PYTHONCOERCECLOCALE=0.\n"
        "Do not use Git history, benchmark metadata, a target issue, a fixed checkout, a patch, or a hidden regression test.\n"
        "The target-specific regression test and changed-file metadata are excluded from this context.\n\n"
    )
    out = ROOT / "data/experiment5_target_context/Tornado-1.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(header + body)
    return out


def make_history() -> tuple[Path, Path]:
    raw_all = json.loads((ROOT / "data/experiment2_historical_raw.json").read_text())
    structured_all = json.loads((ROOT / "data/experiment2_historical_structured.json").read_text())
    raw = [row for row in raw_all if row.get("history_id") in ANALOGUES]
    structured = [row for row in structured_all if row.get("history_id") in ANALOGUES]
    if {row.get("history_id") for row in raw} != set(ANALOGUES):
        raise RuntimeError("selected raw analogue set is incomplete")
    if {row.get("history_id") for row in structured} != set(ANALOGUES):
        raise RuntimeError("selected structured analogue set is incomplete")
    raw_path = ROOT / "data/experiment5_historical_raw.json"
    structured_path = ROOT / "data/experiment5_historical_structured.json"
    raw_path.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n")
    structured_path.write_text(json.dumps(structured, indent=2, ensure_ascii=False) + "\n")
    return raw_path, structured_path


def make_manifest(context: Path, raw: Path, structured: Path) -> Path:
    hidden_test = FIXED / "tornado/test/websocket_test.py"
    manifest = {
        "experiment": "experiment5_second_target_replication",
        "target_id": TARGET_ID,
        "agent_visible": {
            "target_context": str(context.relative_to(ROOT)),
            "historical_raw": str(raw.relative_to(ROOT)),
            "historical_structured": str(structured.relative_to(ROOT)),
            "buggy_checkout": str(BUGGY.relative_to(ROOT)),
            "model": "deepseek-flash",
            "temperature": 0.2,
            "max_output_tokens": 2200,
            "thinking": "disabled",
            "execution_environment": "Python 3.9.18; LC_ALL=C; PYTHONUTF8=0; PYTHONCOERCECLOCALE=0",
        },
        "evaluator_only": {
            "fixed_checkout": str(FIXED.relative_to(ROOT)),
            "bug_info": "vendor/BugsInPy/projects/tornado/bugs/1/bug.info",
            "target_issue": "not exposed; BugsInPy supplies no standalone issue text",
            "target_fix_diff": "vendor/BugsInPy/projects/tornado/bugs/1/bug_patch.txt",
            "hidden_regression_test": "tornado/test/websocket_test.py",
            "hidden_regression_sha256": sha256(hidden_test),
            "changed_file_metadata": ["tornado/websocket.py", "tornado/test/websocket_test.py"],
            "ground_truth": {
                "buggy_revision": "6a5a0bfa370b6c0d3dbbf9589a560a98202d2baa",
                "fixed_revision": "4677c54cc18bbfbdf0f4dadf11610fab6203fd63",
                "true_trigger": "A WebSocketHandler calls set_nodelay(True) during open while the buggy handler's stream is unavailable and the active WebSocket connection is the valid receiver.",
                "expected_invariant": "set_nodelay configures the active WebSocket connection and the handler completes the handshake/message exchange.",
                "actual_failure": "The buggy handler asserts self.stream is not None and the open callback fails before sending the message.",
                "failure_mechanism": "Lifecycle-specific receiver mismatch: WebSocketHandler.set_nodelay dispatches through self.stream instead of self.ws_connection.",
                "oracle": "A local WebSocket handler invoking set_nodelay(True) can send a known message that the client receives.",
                "relevant_code_area": ["tornado/websocket.py:558-562", "tornado/websocket.py:714-718", "tornado/websocket.py:1348-1352"],
            },
        },
        "selected_analogue_set": ANALOGUES,
        "leakage_control": {
            "generation_must_not_read": [
                "evaluator_only",
                "vendor/BugsInPy/projects/tornado/bugs/1/bug.info",
                "vendor/BugsInPy/projects/tornado/bugs/1/bug_patch.txt",
                "workspace/experiment5/tornado-fixed",
                "tornado/test/websocket_test.py",
            ],
            "fixed_checkout_access": "evaluator only after test is frozen and hashed",
        },
    }
    path = ROOT / "data/experiment5_target_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return path


def main() -> None:
    copy_checkout(SOURCE_BUGGY, BUGGY)
    copy_checkout(SOURCE_FIXED, FIXED)
    context = make_context()
    raw, structured = make_history()
    manifest = make_manifest(context, raw, structured)
    print(json.dumps({"target_id": TARGET_ID, "context": str(context.relative_to(ROOT)), "manifest": str(manifest.relative_to(ROOT)), "analogues": ANALOGUES}))


if __name__ == "__main__":
    main()
