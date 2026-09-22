from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from scripts.deepseek_client import DeepSeekClient


ROOT = Path(__file__).resolve().parents[1]
CONDITIONS = {"A": "TARGET_ONLY", "B": "NAIVE_RAW_HISTORY", "C": "STRUCTURED_APPLICABILITY_AWARE"}
REQUIRED_HYPOTHESIS_FIELDS = {"claim", "trigger", "expected_invariant", "oracle", "oracle_evidence"}


def parse_model_output(content: str) -> dict:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    parsed = json.loads(content)
    status = parsed.get("status")
    if status == "NO_SUPPORTED_HYPOTHESIS":
        return {"status": status, "applicability": parsed.get("applicability", []), "hypothesis": None, "test_code": ""}
    # Some otherwise valid model responses use the applicability label as the
    # top-level status. If a complete hypothesis is present, normalize it to
    # the experiment's candidate status instead of discarding the candidate.
    if status != "HYPOTHESIS" and not parsed.get("hypothesis"):
        raise ValueError("status must be HYPOTHESIS or NO_SUPPORTED_HYPOTHESIS")
    hypothesis = parsed.get("hypothesis") or {}
    missing = REQUIRED_HYPOTHESIS_FIELDS - set(hypothesis)
    if missing:
        raise ValueError(f"hypothesis missing fields: {sorted(missing)}")
    test_code = parsed.get("test_code", "")
    if not isinstance(test_code, str) or "assert" not in test_code:
        raise ValueError("test_code must contain a meaningful assertion")
    lowered = test_code.lower()
    if "assert false" in lowered or "mock.patch" in lowered or "unittest.mock" in lowered or "git log" in lowered or "bugsinpy_" in lowered:
        raise ValueError("test code violates executable-test constraints")
    return {"status": "HYPOTHESIS", "applicability": parsed.get("applicability", []), "hypothesis": hypothesis, "test_code": test_code}


def compact_raw(record: dict) -> str:
    return json.dumps({k: record.get(k) for k in ["history_id", "bug_report", "commit_subject", "fix_summary", "regression_test_summary", "source_references"]}, ensure_ascii=False)


def compact_structured(record: dict) -> str:
    return json.dumps({"history_id": record["history_id"], **{field: record[field] for field in ["Context", "Preconditions", "Trigger", "Expected Invariant", "Observed Failure", "Failure Mechanism", "Oracle", "Oracle Provenance", "Test Strategy", "Evidence References", "Confidence"]}}, ensure_ascii=False)


def prompt_for(condition: str, target_id: str, target_context: str, raw: list[dict], structured: list[dict], attempt: int) -> str:
    common = f"""Target: {target_id}\nAttempt: {attempt}\n\nTARGET CONTEXT (the only target-side information available):\n{target_context}\n\nYou must propose at most one falsifiable hypothesis and at most one minimal pytest test. The test must exercise real target code, use a deterministic meaningful assertion, and avoid mocks, benchmark metadata, Git history, fixed revisions, or hidden bug details. Do not treat current implementation behavior as the oracle. Prefer NO_SUPPORTED_HYPOTHESIS when the oracle is unsupported. Return JSON only with keys: status, applicability, hypothesis, test_code. A hypothesis object must contain claim, trigger, expected_invariant, oracle, oracle_evidence.\n"""
    if condition == "A":
        return common + "No historical knowledge is provided. Reason only from target context, ordinary docs, and ordinary tests."
    if condition == "B":
        return common + "RAW HISTORICAL EVIDENCE (same candidate IDs used by condition C):\n" + "\n".join(compact_raw(r) for r in raw)
    return common + "STRUCTURED HISTORICAL BUG KNOWLEDGE UNITS (same candidate IDs used by condition B):\n" + "\n".join(compact_structured(r) for r in structured) + "\n\nFor each historical unit, make a bounded applicability decision of SUPPORTED, WEAK, or NOT_APPLICABLE. A historical invariant alone cannot confirm target truth. If no unit supports a grounded target oracle, return NO_SUPPORTED_HYPOTHESIS."


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "data" / "case_manifest.json")
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--conditions", default="A,B,C")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    target = manifest["target"]
    target_id = target["target_id"]
    context = Path(target["target_context"]).read_text()
    raw = json.loads((ROOT / "data" / "historical_raw.json").read_text())
    structured = json.loads((ROOT / "data" / "historical_structured.json").read_text())
    output_root = ROOT / "artifacts" / "llm" / target_id.replace(":", "_")
    tests_root = ROOT / "generated_tests" / target_id.replace(":", "_")
    output_root.mkdir(parents=True, exist_ok=True)
    tests_root.mkdir(parents=True, exist_ok=True)
    client = DeepSeekClient(model=manifest["model"]["name"], temperature=manifest["model"]["temperature"])
    for condition in [c.strip() for c in args.conditions.split(",") if c.strip()]:
        for attempt in range(1, args.attempts + 1):
            prompt = prompt_for(condition, target_id, context, raw, structured, attempt)
            prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
            repair_attempts = 0
            parse_error = None
            result = None
            parsed = None
            for repair_attempts in range(2):
                try:
                    result = client.generate(prompt, max_tokens=manifest["model"]["max_tokens"])
                    parsed = parse_model_output(result.content)
                    parse_error = None
                    break
                except Exception as exc:
                    parse_error = str(exc)
                    prompt = prompt + "\nRepair the previous response. Output valid JSON matching the schema and do not add prose."
            record = {
                "target_id": target_id,
                "condition": condition,
                "condition_name": CONDITIONS[condition],
                "attempt": attempt,
                "prompt_sha256": prompt_hash,
                "repair_attempts": repair_attempts,
                "parse_error": parse_error,
                "llm": result.log_record if result else {"model": manifest["model"]["name"], "request_count": 0},
                "raw_response": result.content if result else "",
                "status": parsed["status"] if parsed else "MECHANICAL_FAILURE",
                "applicability": parsed.get("applicability", []) if parsed else [],
                "hypothesis": parsed.get("hypothesis") if parsed else None,
                "test_path": None,
            }
            if parsed and parsed["status"] == "HYPOTHESIS":
                test_path = tests_root / f"{condition}_attempt_{attempt}.py"
                test_path.write_text(parsed["test_code"])
                record["test_path"] = str(test_path.relative_to(ROOT))
            artifact = output_root / f"{condition}_attempt_{attempt}.json"
            artifact.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
            print(json.dumps({"condition": condition, "attempt": attempt, "status": record["status"], "test": bool(record["test_path"]), "repair_attempts": repair_attempts}))


if __name__ == "__main__":
    main()
