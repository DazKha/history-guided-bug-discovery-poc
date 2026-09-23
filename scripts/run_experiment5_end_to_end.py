from __future__ import annotations

"""Generate Experiment 5A candidates using the unchanged Experiment 2 style."""

import argparse
import hashlib
import json
import re
import time
from pathlib import Path

try:
    from .deepseek_client import DeepSeekClient
except ImportError:
    from deepseek_client import DeepSeekClient


ROOT = Path(__file__).resolve().parents[1]
CONDITIONS = {"A": "TARGET_ONLY", "B": "NAIVE_RAW_HISTORY", "C": "STRUCTURED_APPLICABILITY_AWARE"}
ATTEMPTS = 10
MAX_TOKENS = 2200


def _json(value: object) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False)


def prompt_for(condition: str, context: str, raw: list[dict], structured: list[dict], attempt: int) -> str:
    prompt = """You are generating one falsifiable proactive bug-discovery candidate for a real Python repository.

Rules:
- Use only the supplied target context and, where supplied, historical evidence.
- Do not use Git history, benchmark metadata, the target issue, the target fixed revision, hidden regression tests, or hidden changed-file metadata.
- Generate exactly ONE strongest target-specific functional-bug hypothesis and exactly ONE minimal executable test.
- The test must exercise real target code, use a deterministic meaningful assertion, and not use mocks to manufacture failure.
- If the suspected defect may raise an exception, catch that expected target exception in the test and assert the intended no-error/output invariant; an unhandled target exception alone is mechanical.
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
  "test_code": "complete executable test module as a string, or empty only when status is NO_SUPPORTED_HYPOTHESIS",
  "test_file_path": "generated_tests/experiment5/end_to_end/CONDITION_attempt_N.py, or empty only when status is NO_SUPPORTED_HYPOTHESIS",
  "applicability_decisions": []
}
"""
    prompt += f"\nThis is attempt {attempt} of {ATTEMPTS}. The condition is {condition} ({CONDITIONS[condition]}).\n"
    prompt += "\n===== SAME TARGET CONTEXT FOR ALL CONDITIONS =====\n" + context
    if condition == "A":
        prompt += "\n===== NO HISTORICAL EVIDENCE IN THIS CONDITION =====\nForm the strongest plausible test from the target context. Do not abstain merely because the target issue is hidden.\n"
    elif condition == "B":
        prompt += "\n===== RAW HISTORICAL BUG EVIDENCE =====\n" + _json(raw)
        prompt += "\nThese examples may or may not transfer. This is intentionally a naive raw-history baseline; use target-side evidence for the oracle and attempt a concrete target test when possible.\n"
    else:
        prompt += "\n===== STRUCTURED HISTORICAL BUG KNOWLEDGE =====\n" + _json(structured)
        prompt += "\nEvaluate each historical unit with SUPPORTED, WEAK, or NOT_APPLICABLE decisions by comparing context, preconditions, trigger feasibility, failure mechanism, invariant meaning, and target-side oracle support. Generate a concrete test when target evidence supports one.\n"
    return prompt


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
    obj["oracle"] = {"expected_behavior": str(oracle.get("expected_behavior") or ""), "target_evidence": str(oracle.get("target_evidence") or ""), "historical_evidence": str(oracle.get("historical_evidence") or ""), "confidence": oracle.get("confidence", 0)}
    obj["test_code"] = str(obj.get("test_code") or "")
    obj["test_file_path"] = str(obj.get("test_file_path") or "")
    obj["applicability_decisions"] = obj.get("applicability_decisions") or []
    if status == "TEST":
        if not obj["hypothesis"] or not obj["test_code"]:
            raise ValueError("TEST response is missing hypothesis or test_code")
        lowered = obj["test_code"].lower()
        forbidden = ["assert false", "pytest.fail", "git log", "git show", "bugsinpy", "websocket_test.py"]
        if any(token in lowered for token in forbidden):
            raise ValueError("test contains forbidden construction")
    return obj


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempts", type=int, default=ATTEMPTS)
    args = parser.parse_args()
    attempts = ATTEMPTS if args.attempts == ATTEMPTS else max(1, min(args.attempts, ATTEMPTS))
    manifest = json.loads((ROOT / "data/experiment5_target_manifest.json").read_text())
    visible = manifest["agent_visible"]
    context = (ROOT / visible["target_context"]).read_text()
    raw = json.loads((ROOT / visible["historical_raw"]).read_text())
    structured = json.loads((ROOT / visible["historical_structured"]).read_text())
    client = DeepSeekClient(model=visible["model"], temperature=visible["temperature"])
    out_root = ROOT / "artifacts/experiment5/end_to_end"
    test_root = ROOT / "generated_tests/experiment5/end_to_end"
    out_root.mkdir(parents=True, exist_ok=True)
    test_root.mkdir(parents=True, exist_ok=True)
    for condition in CONDITIONS:
        for attempt in range(1, attempts + 1):
            started = time.time()
            prompt = prompt_for(condition, context, raw, structured, attempt)
            record = {
                "experiment": "experiment5_end_to_end",
                "target_id": "tornado:1",
                "condition": condition,
                "condition_name": CONDITIONS[condition],
                "attempt": attempt,
                "attempt_id": f"experiment5_{condition}_{attempt:02d}",
                "status": "MODEL_ERROR",
                "repair_attempts": 0,
                "generation_visible_files": [visible["target_context"]] + ([visible["historical_raw"]] if condition == "B" else [visible["historical_structured"]] if condition == "C" else []),
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            }
            (out_root / condition).mkdir(parents=True, exist_ok=True)
            (out_root / condition / f"attempt_{attempt:02d}.prompt.txt").write_text(prompt)
            try:
                response = client.generate(prompt, max_tokens=MAX_TOKENS)
                parsed = parse_model(response.content)
                record.update(parsed, llm=response.log_record)
                if parsed["status"] == "TEST":
                    path = test_root / condition / f"attempt_{attempt:02d}.py"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(parsed["test_code"] + "\n")
                    record.update({"test_path": str(path.relative_to(ROOT)), "test_sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
                else:
                    record["test_path"] = ""
            except Exception as exc:
                record.update({"error": str(exc)[:1000], "llm": {"model": client.model, "request_count": client.request_count, "usage": {}}})
            record["wall_clock_seconds"] = round(time.time() - started, 3)
            (out_root / condition / f"attempt_{attempt:02d}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
            print(json.dumps({"attempt_id": record["attempt_id"], "status": record["status"], "test": bool(record.get("test_path")), "request_count": client.request_count}))
    print(json.dumps({"experiment": "experiment5_end_to_end", "attempts_per_condition": attempts, "requests": client.request_count}))


if __name__ == "__main__":
    main()
