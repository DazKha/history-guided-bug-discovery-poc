from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

try:
    from .deepseek_client import DeepSeekClient
    from .experiment3_runner import freeze_hypothesis, hypothesis_prompt, parse_test_response, test_prompt
    from .experiment3_trigger_planner import build_trigger_prompt, parse_trigger_response
    from .run_experiment2 import parse_model
except ImportError:
    from deepseek_client import DeepSeekClient
    from experiment3_runner import freeze_hypothesis, hypothesis_prompt, parse_test_response, test_prompt
    from experiment3_trigger_planner import build_trigger_prompt, parse_trigger_response
    from run_experiment2 import parse_model


ROOT = Path(__file__).resolve().parents[1]
TARGET_ID = "PySnooper:1"
TARGET_CONTEXT = ROOT / "data/experiment2_target_context/PySnooper-1.txt"
HISTORY = ROOT / "data/experiment2_historical_structured.json"
MODEL = "deepseek-flash"
TEMPERATURE = 0.2
MAX_TOKENS = 2200
MAX_REPAIRS = 1


def hypothesis_only_prompt(context: str, history: list[dict[str, Any]], attempt: int) -> str:
    return f"""Use the target context and structured historical Bug Knowledge Units to generate exactly one grounded hypothesis, but do not generate a test yet.

This is hypothesis stage attempt {attempt}. Evaluate applicability as SUPPORTED, WEAK, or NOT_APPLICABLE. Freeze the claim, trigger idea, potential failure, and target-supported oracle for later trigger planning. Do not use issue text, fixed source, diffs, hidden regression tests, benchmark metadata, or evaluator truth. Return JSON only in the existing Experiment 2 schema with status TEST or NO_SUPPORTED_HYPOTHESIS and an empty test_code.

===== TARGET CONTEXT =====
{context}
===== STRUCTURED HISTORY =====
{json.dumps(history, ensure_ascii=False, indent=2)}
"""


def parse_hypothesis_only(content: str, attempt: int) -> dict[str, Any]:
    obj = parse_model(content)
    obj["test_code"] = ""
    obj["test_file_path"] = ""
    obj["attempt"] = attempt
    if obj["status"] == "TEST":
        if not obj.get("hypothesis") or not obj.get("oracle", {}).get("expected_behavior"):
            raise ValueError("hypothesis stage response lacks claim or oracle")
    return obj


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def _write_json(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")


def _llm_meta(client: DeepSeekClient, result: Any) -> dict[str, Any]:
    return result.log_record


def _hypothesis_id(mode: str, index: int, record: dict[str, Any]) -> str:
    digest = record.get("hypothesis_sha256", "")[:10]
    return f"{mode}-h{index:02d}-{digest}"


def generate_hypotheses(mode: str, attempts: int, client: DeepSeekClient | None = None) -> list[dict[str, Any]]:
    context = TARGET_CONTEXT.read_text()
    history = json.loads(HISTORY.read_text())
    out = ROOT / "artifacts/experiment3_llm" / mode / "hypotheses"
    out.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    conditional = ROOT / "data/experiment3_conditional_hypotheses.json"
    if mode == "conditional":
        source = json.loads(conditional.read_text())
        for index, raw in enumerate(source[:attempts], 1):
            record = freeze_hypothesis(raw)
            record.update({"experiment": "experiment3", "mode": mode, "attempt": index, "generation_visible_files": [str(TARGET_CONTEXT.relative_to(ROOT)), str(HISTORY.relative_to(ROOT))]})
            record["hypothesis_id"] = _hypothesis_id(mode, index, record)
            _write_json(out / f"{record['hypothesis_id']}.json", record)
            records.append(record)
        return records
    if client is None:
        client = DeepSeekClient(model=MODEL, temperature=TEMPERATURE)
    for attempt in range(1, attempts + 1):
        started = time.time()
        record: dict[str, Any] = {
            "experiment": "experiment3", "mode": mode, "attempt": attempt, "status": "MODEL_ERROR",
            "generation_visible_files": [str(TARGET_CONTEXT.relative_to(ROOT)), str(HISTORY.relative_to(ROOT))],
        }
        try:
            result = client.generate(hypothesis_only_prompt(context, history, attempt), max_tokens=MAX_TOKENS)
            parsed = parse_hypothesis_only(result.content, attempt)
            record.update(parsed)
            record["llm"] = _llm_meta(client, result)
            if parsed["status"] == "TEST":
                frozen = freeze_hypothesis(record)
                record.update(frozen)
                record["hypothesis_id"] = _hypothesis_id(mode, attempt, record)
        except Exception as exc:
            record["error"] = str(exc)[:500]
            record["llm"] = {"model": client.model, "request_count": client.request_count, "usage": {}}
        record["wall_clock_seconds"] = round(time.time() - started, 3)
        _write_json(out / f"{mode}_h{attempt:02d}.json", record)
        records.append(record)
    return records


def generate_c1(record: dict[str, Any], client: DeepSeekClient, context: str, out_root: Path, test_root: Path) -> dict[str, Any]:
    started = time.time()
    result_record = {"experiment": "experiment3", "mode": record["mode"], "arm": "C1", "hypothesis_id": record["hypothesis_id"], "hypothesis": record["hypothesis"], "trigger": record.get("trigger", ""), "oracle": record.get("oracle", {}), "hypothesis_sha256": record["hypothesis_sha256"], "hypothesis_frozen": True, "generation_visible_files": record["generation_visible_files"], "repair_attempts": 0}
    try:
        response = client.generate(hypothesis_prompt(record), max_tokens=MAX_TOKENS)
        parsed = parse_test_response(response.content)
        result_record.update(parsed)
        result_record["llm"] = response.log_record
        if parsed["status"] == "TEST":
            test_id = f"{record['hypothesis_id']}-direct"
            path = test_root / f"{_safe_name(test_id)}.py"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(parsed["test_code"] + "\n")
            result_record.update({"test_id": test_id, "test_path": str(path.relative_to(ROOT)), "test_sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    except Exception as exc:
        result_record.update({"status": "MODEL_ERROR", "error": str(exc)[:500], "llm": {"model": client.model, "request_count": client.request_count, "usage": {}}})
    result_record["wall_clock_seconds"] = round(time.time() - started, 3)
    _write_json(out_root / f"{_safe_name(record['hypothesis_id'])}__C1.json", result_record)
    return result_record


def generate_c2(record: dict[str, Any], client: DeepSeekClient, context: str, history: list[dict[str, Any]], out_root: Path, test_root: Path) -> list[dict[str, Any]]:
    planner_started = time.time()
    base = {"experiment": "experiment3", "mode": record["mode"], "arm": "C2", "hypothesis_id": record["hypothesis_id"], "hypothesis": record["hypothesis"], "trigger": record.get("trigger", ""), "oracle": record.get("oracle", {}), "hypothesis_sha256": record["hypothesis_sha256"], "hypothesis_frozen": True, "generation_visible_files": record["generation_visible_files"], "repair_attempts": 0}
    try:
        planner_response = client.generate(build_trigger_prompt(record, context, history, count=4), max_tokens=MAX_TOKENS)
        triggers = parse_trigger_response(planner_response.content)
        planner_meta = planner_response.log_record
    except Exception as exc:
        failed = dict(base, status="TRIGGER_PLANNER_ERROR", error=str(exc)[:500], llm={"model": client.model, "request_count": client.request_count, "usage": {}}, planner_wall_clock_seconds=round(time.time() - planner_started, 3))
        _write_json(out_root / f"{_safe_name(record['hypothesis_id'])}__C2_planner.json", failed)
        return [failed]
    _write_json(out_root / f"{_safe_name(record['hypothesis_id'])}__C2_planner.json", dict(base, status="TRIGGERS", triggers=triggers, llm=planner_meta, planner_wall_clock_seconds=round(time.time() - planner_started, 3)))
    results = []
    for trigger in triggers:
        started = time.time()
        result_record = dict(base, trigger_id=trigger["trigger_id"], trigger_plan=trigger)
        try:
            response = client.generate(test_prompt(record, trigger, context), max_tokens=MAX_TOKENS)
            parsed = parse_test_response(response.content)
            result_record.update(parsed, llm=response.log_record)
            if parsed["status"] == "TEST":
                test_id = f"{record['hypothesis_id']}-{_safe_name(trigger['trigger_id'])}"
                path = test_root / f"{_safe_name(test_id)}.py"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(parsed["test_code"] + "\n")
                result_record.update({"test_id": test_id, "test_path": str(path.relative_to(ROOT)), "test_sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        except Exception as exc:
            result_record.update({"status": "MODEL_ERROR", "error": str(exc)[:500], "llm": {"model": client.model, "request_count": client.request_count, "usage": {}}})
        result_record["wall_clock_seconds"] = round(time.time() - started, 3)
        _write_json(out_root / f"{_safe_name(record['hypothesis_id'])}__{_safe_name(trigger['trigger_id'])}.json", result_record)
        results.append(result_record)
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["natural", "conditional"], default="natural")
    parser.add_argument("--arm", choices=["C1", "C2", "both"], default="both")
    parser.add_argument("--attempts", type=int, default=5)
    args = parser.parse_args()
    attempts = max(1, args.attempts)
    client = DeepSeekClient(model=MODEL, temperature=TEMPERATURE)
    hypotheses = generate_hypotheses(args.mode, attempts, client if args.mode == "natural" else None)
    context = TARGET_CONTEXT.read_text()
    history = json.loads(HISTORY.read_text())
    for record in hypotheses:
        if record.get("status") != "TEST":
            continue
        if args.arm in {"C1", "both"}:
            generate_c1(record, client, context, ROOT / "artifacts/experiment3_llm" / args.mode / "C1", ROOT / "generated_tests/experiment3" / args.mode / "C1")
        if args.arm in {"C2", "both"}:
            generate_c2(record, client, context, history, ROOT / "artifacts/experiment3_llm" / args.mode / "C2", ROOT / "generated_tests/experiment3" / args.mode / "C2")


if __name__ == "__main__":
    main()

