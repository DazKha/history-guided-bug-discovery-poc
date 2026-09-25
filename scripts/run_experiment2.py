from __future__ import annotations

"""Run Experiment 2 generation using agent-visible files only.

This module intentionally has no import or path reference to evaluator truth.
It produces one JSON response and at most one generated test per attempt.
"""

import argparse
import json
import re
import time
from pathlib import Path

try:  # package import for tests; direct-script import for reproduction commands
    from .deepseek_client import DeepSeekClient
except ImportError:
    from deepseek_client import DeepSeekClient


ROOT = Path(__file__).resolve().parents[1]
CONDITIONS = {
    "A": "TARGET_ONLY",
    "B": "NAIVE_RAW_HISTORY",
    "C": "STRUCTURED_APPLICABILITY_AWARE",
}
MAX_ATTEMPTS = 5
MAX_REPAIRS = 1
RUN_LABEL_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")


def _json(value: object) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False)


def base_instructions() -> str:
    return """You are generating one falsifiable proactive bug-discovery candidate for a real Python repository.

Rules:
- Use only the supplied target context and, where supplied, historical evidence.
- Do not use Git history, benchmark metadata, the target issue, the target fixed revision, hidden regression tests, or hidden changed-file metadata.
- Generate exactly ONE strongest target-specific functional-bug hypothesis and exactly ONE minimal pytest test.
- The test must exercise real target code, use a deterministic meaningful assertion, and not use mocks to manufacture failure.
- If the suspected defect may raise an exception, catch that expected target exception in the test and assert the intended no-error/output invariant; an unhandled target exception alone will be classified as mechanical rather than as a meaningful assertion failure.
- Do not use assert False, pytest.fail, Git, benchmark metadata, or a hidden regression path.
- The oracle must be justified by target-side source/docs/ordinary-test evidence when possible. Historical evidence can suggest what to probe but cannot by itself establish target truth.
- Return JSON only, with no Markdown fences, using the requested schema.

Schema:
{
  "status": "TEST" | "NO_SUPPORTED_HYPOTHESIS",
  "hypothesis": "one concrete falsifiable claim",
  "trigger": "minimal target input/setup that should expose it",
  "potential_failure": "what semantic behavior may fail",
  "oracle": {
    "expected_behavior": "meaningful expected behavior",
    "target_evidence": "specific target source/docs/ordinary test/runtime evidence",
    "historical_evidence": "which historical evidence informed this, or empty",
    "confidence": 0.0
  },
  "test_code": "complete pytest module as a string, or empty only when status is NO_SUPPORTED_HYPOTHESIS",
  "test_file_path": "generated_tests/experiment2/PySnooper_1/CONDITION_attempt_N.py, or empty only when status is NO_SUPPORTED_HYPOTHESIS",
  "applicability_decisions": []
}
"""


def prompt_for(condition: str, context: str, raw: list[dict], structured: list[dict], attempt: int) -> str:
    prompt = base_instructions()
    prompt += f"\nThis is attempt {attempt} of 5. The condition is {condition} ({CONDITIONS[condition]}).\n"
    prompt += "\n===== SAME TARGET CONTEXT FOR ALL CONDITIONS =====\n" + context
    if condition == "A":
        prompt += "\n===== NO HISTORICAL EVIDENCE IN THIS CONDITION =====\n"
        prompt += "Form your strongest plausible test from the target context. Do not abstain merely because the target issue is hidden; abstain only if no concrete assertion can be formed from the supplied target evidence.\n"
    elif condition == "B":
        prompt += "\n===== RAW HISTORICAL BUG EVIDENCE =====\n" + _json(raw)
        prompt += """
These historical bugs are examples that may or may not transfer. This is intentionally a naive raw-history baseline: use the raw reports, fix diffs, and regression-test evidence to generate your best plausible target-specific hypothesis and test. Do not apply an explicit applicability gate and do not abstain simply because the target issue is hidden. You may reject obviously irrelevant evidence, but attempt a concrete target test when the target source supports one.
"""
    else:
        prompt += "\n===== STRUCTURED HISTORICAL BUG KNOWLEDGE =====\n" + _json(structured)
        prompt += """
Evaluate each historical unit against this target with bounded decisions SUPPORTED, WEAK, or NOT_APPLICABLE. For each decision, compare context, preconditions, trigger feasibility, failure mechanism, invariant meaning, and target-side oracle support. Historical knowledge suggests what to probe; it does not define target truth. You may return NO_SUPPORTED_HYPOTHESIS if no unit has enough support for a target-specific oracle. If a unit is supported or weak but the target context supplies a meaningful oracle, generate the strongest one test. Put the decisions and reasons in applicability_decisions.
"""
    return prompt


def validate_run_label(label: str) -> str:
    """Validate the single path component used to isolate a live run."""

    if not isinstance(label, str) or not RUN_LABEL_PATTERN.fullmatch(label):
        raise ValueError(
            "run label must be a non-empty path component containing only "
            "letters, numbers, '.', '-', or '_'"
        )
    return label


def ensure_fresh_run_paths(output_root: Path, test_root: Path) -> None:
    """Refuse to reuse either live-run output location."""

    existing = [str(path) for path in (output_root, test_root) if path.exists()]
    if existing:
        raise ValueError(
            "refusing to reuse existing Experiment 2 output path(s): "
            + ", ".join(existing)
            + "; choose a new --run-label"
        )


def parse_model(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("response did not contain a JSON object")
    obj = json.loads(text[start:end + 1])
    status = str(obj.get("status", "")).upper()
    if status in {"HYPOTHESIS", "SUPPORTED", "TEST"}:
        status = "TEST"
    elif status in {"NO_SUPPORTED_HYPOTHESIS", "NO_HYPOTHESIS", "NOT_APPLICABLE", "ABSTAIN"}:
        status = "NO_SUPPORTED_HYPOTHESIS"
    else:
        raise ValueError(f"unsupported status: {status}")
    oracle = obj.get("oracle") or {}
    obj["status"] = status
    obj["hypothesis"] = str(obj.get("hypothesis") or "")
    obj["trigger"] = str(obj.get("trigger") or "")
    obj["potential_failure"] = str(obj.get("potential_failure") or "")
    obj["oracle"] = {
        "expected_behavior": str(oracle.get("expected_behavior") or ""),
        "target_evidence": str(oracle.get("target_evidence") or ""),
        "historical_evidence": str(oracle.get("historical_evidence") or ""),
        "confidence": oracle.get("confidence", 0),
    }
    obj["test_code"] = str(obj.get("test_code") or "")
    obj["test_file_path"] = str(obj.get("test_file_path") or "")
    obj["applicability_decisions"] = obj.get("applicability_decisions") or []
    if status == "TEST":
        if not obj["hypothesis"] or not obj["test_code"]:
            raise ValueError("TEST response is missing hypothesis or test_code")
        lowered = obj["test_code"].lower()
        forbidden = ["assert false", "pytest.fail", "git log", "git show", "bugsinpy", "test_chinese.py"]
        if any(token in lowered for token in forbidden):
            raise ValueError("test contains forbidden construction")
    return obj


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempts", type=int, default=MAX_ATTEMPTS)
    parser.add_argument("--condition", choices=["A", "B", "C"], action="append")
    parser.add_argument("--run-label", required=True, help="new artifact/test suffix; it must not already exist")
    args = parser.parse_args()
    attempts = min(max(args.attempts, 1), MAX_ATTEMPTS)
    selected = args.condition or list(CONDITIONS)
    try:
        run_label = validate_run_label(args.run_label)
    except ValueError as exc:
        parser.error(str(exc))
    context = (ROOT / "data/experiment2_target_context/PySnooper-1.txt").read_text()
    raw = json.loads((ROOT / "data/experiment2_historical_raw.json").read_text())
    structured = json.loads((ROOT / "data/experiment2_historical_structured.json").read_text())
    suffix = f"_{run_label}"
    run_output_root = ROOT / f"artifacts/experiment2_llm{suffix}"
    run_test_root = ROOT / f"generated_tests/experiment2{suffix}"
    try:
        ensure_fresh_run_paths(run_output_root, run_test_root)
    except ValueError as exc:
        parser.error(str(exc))
    out_root = run_output_root / "PySnooper_1"
    test_root = run_test_root / "PySnooper_1"
    out_root.mkdir(parents=True, exist_ok=True)
    test_root.mkdir(parents=True, exist_ok=True)
    client = DeepSeekClient(model="deepseek-flash", temperature=0.2)
    all_records = []
    for condition in selected:
        for attempt in range(1, attempts + 1):
            started = time.time()
            record = {
                "experiment": "experiment2_transfer_feasibility",
                "target_id": "PySnooper:1",
                "condition": condition,
                "condition_name": CONDITIONS[condition],
                "attempt": attempt,
                "status": "MODEL_ERROR",
                "repair_attempts": 0,
                "generation_visible_files": ["data/experiment2_target_context/PySnooper-1.txt"] + (["data/experiment2_historical_raw.json"] if condition == "B" else ["data/experiment2_historical_structured.json"] if condition == "C" else []),
            }
            try:
                result = client.generate(prompt_for(condition, context, raw, structured, attempt), max_tokens=2200)
                parsed = parse_model(result.content)
                record.update(parsed)
                record["llm"] = result.log_record
                if parsed["status"] == "TEST":
                    test_name = f"{condition}_attempt_{attempt}.py"
                    test_path = test_root / test_name
                    test_path.write_text(parsed["test_code"] + "\n")
                    record["test_path"] = str(test_path.relative_to(ROOT))
                    record["test_file_path"] = record["test_path"]
                else:
                    record["test_path"] = ""
            except Exception as exc:
                record["error"] = str(exc)[:500]
                record["llm"] = {"model": client.model, "request_count": client.request_count, "latency_seconds": round(time.time() - started, 3), "usage": {}}
            record.setdefault("llm", {"model": client.model, "request_count": client.request_count, "latency_seconds": round(time.time() - started, 3), "usage": {}})
            record["wall_clock_seconds"] = round(time.time() - started, 3)
            artifact = out_root / f"{condition}_attempt_{attempt}.json"
            artifact.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
            all_records.append(record)
            print(json.dumps({"condition": condition, "attempt": attempt, "status": record["status"], "test": bool(record.get("test_path")), "request_count": client.request_count}))
    (out_root / "run_manifest.json").write_text(json.dumps({"conditions": selected, "attempts": attempts, "model": client.model, "temperature": 0.2, "max_tokens": 2200, "records": len(all_records)}, indent=2) + "\n")


if __name__ == "__main__":
    main()
