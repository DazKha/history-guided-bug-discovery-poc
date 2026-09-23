from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

try:
    from .deepseek_client import DeepSeekClient
    from .experiment3_runner import freeze_hypothesis, hypothesis_prompt, parse_test_response, test_prompt
    from .experiment4_plan_contract import parse_plan_response
except ImportError:
    from deepseek_client import DeepSeekClient
    from experiment3_runner import freeze_hypothesis, hypothesis_prompt, parse_test_response, test_prompt
    from experiment4_plan_contract import parse_plan_response


ROOT = Path(__file__).resolve().parents[1]
TARGET_CONTEXT = ROOT / "data/experiment2_target_context/PySnooper-1.txt"
HISTORY = ROOT / "data/experiment2_historical_structured.json"
SOURCE_HYPOTHESES = ROOT / "data/experiment3_conditional_hypotheses.json"
MODEL = "deepseek-flash"
TEMPERATURE = 0.2
MAX_TOKENS = 2200
MAX_REPAIRS = 2
PLAN_COUNT = 3


def plan_test_prompt(hypothesis: dict[str, Any], plan: dict[str, Any], target_context: str, iteration: int) -> str:
    if iteration >= 3:
        visible = {key: hypothesis.get(key, "") for key in ("hypothesis_id", "hypothesis", "trigger", "potential_failure", "oracle")}
        return f"""Generate one compact, complete pytest module from this frozen hypothesis and validated plan.
Return exactly one JSON object with status TEST and test_code, with no markdown or explanation. Keep the hypothesis and oracle unchanged. Use only public APIs and the supplied buggy target context; never use fixed source, patches, issue text, hidden tests, evaluator results, or benchmark paths. Define every name in each module/subprocess scope, declare fixtures, use relative temporary paths, and capture/decode subprocess bytes before comparing text. Execute setup, invoke, observe, then assert the stated invariant. Do not force failure or assert an unrelated value.

FROZEN HYPOTHESIS:
{json.dumps(visible, ensure_ascii=False, separators=(',', ':'))}
VALIDATED PLAN:
{json.dumps(plan, ensure_ascii=False, separators=(',', ':'))}
TARGET CONTEXT:
{target_context}
"""
    checks = """
Before returning code, verify generically that every name used by a generated
module or child subprocess is defined in that scope, every fixture is either a
standard pytest fixture or declared in the module, and the module can be
collected without importing a name from the surrounding prompt. If a child
process emits text under a restricted encoding, capture bytes and decode them
explicitly before writing or comparing text. Do not use absolute repository
paths. Reach the preconditions instead of silently skipping them, but skip only
when a stated environment precondition is unavailable. Assert the stated
observable at its measurement point; do not assert an unrelated intermediate
value or force a failure.
"""
    if iteration >= 2:
        checks += "\nUse one explicit observation variable and make the assertion predicate directly compare it with the expected invariant. Keep setup, invocation, observation, and assertion in the same executable scope."
    visible = {key: hypothesis.get(key, "") for key in ("hypothesis_id", "hypothesis", "trigger", "potential_failure", "oracle")}
    return f"""Generate one complete deterministic pytest module from the frozen hypothesis and validated trigger plan below.

Keep the hypothesis, expected behavior, and oracle unchanged. Use only public target APIs and the visible buggy target context. Do not inspect or mention fixed source, patches, issue reports, hidden tests, benchmark metadata, or evaluator results. Return JSON only with status TEST or NO_SUPPORTED_HYPOTHESIS and test_code.

{checks}

FROZEN HYPOTHESIS:
{json.dumps(visible, ensure_ascii=False, indent=2)}

VALIDATED TRIGGER PLAN:
{json.dumps(plan, ensure_ascii=False, indent=2)}

TARGET CONTEXT:
{target_context}
"""


def validate_generated_test_code(code: str) -> str:
    """Reject syntactically malformed test modules before target execution."""
    try:
        tree = ast.parse(code)
        compile(tree, "<experiment4-generated>", "exec")
    except (SyntaxError, ValueError, TypeError) as exc:
        raise ValueError(f"generated test is not syntactically executable: {exc}") from exc
    if not any(isinstance(node, ast.Assert) for node in ast.walk(tree)):
        raise ValueError("generated test contains no assertion")
    return code


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def _write_json(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")


def load_frozen_hypotheses() -> list[dict[str, Any]]:
    records = []
    for index, raw in enumerate(json.loads(SOURCE_HYPOTHESES.read_text())[:5], 1):
        record = freeze_hypothesis(raw)
        digest = record["hypothesis_sha256"][:10]
        record.update({
            "experiment": "experiment4",
            "mode": "conditional",
            "attempt": index,
            "hypothesis_id": f"conditional-h{index:02d}-{digest}",
            "hypothesis_frozen": True,
            "generation_visible_files": [
                str(TARGET_CONTEXT.relative_to(ROOT)),
                str(HISTORY.relative_to(ROOT)),
            ],
        })
        records.append(record)
    return records


def plan_prompt(hypothesis: dict[str, Any], target_context: str, history: list[dict[str, Any]], iteration: int, feedback: str = "") -> str:
    visible = {key: hypothesis.get(key, "") for key in ("hypothesis_id", "hypothesis", "trigger", "potential_failure", "oracle")}
    refinement = {
        1: "Use the strict contract exactly. Keep each plan compact but executable.",
        2: "Before returning each plan, check that its assertion predicate names the observable and expected invariant, and that the measurement point is after the invoke action.",
        3: "Before returning each plan, check the full state transition: setup/initial state, trigger action, invocation, observation, and a failure condition that cannot pass for an unrelated reason.",
    }.get(iteration, "Use the strict contract exactly.")
    schema = {
        "hypothesis_id": "same frozen id",
        "preconditions": ["concrete condition"],
        "initial_state": {"named_state": "value or condition"},
        "actions": [
            {"type": "create_input|set_environment|initialize_state|invoke|observe", "description": "concrete action"}
        ],
        "expected_invariant": "one observable expected behavior",
        "observable": {"source": "public target source or API named in context", "measurement_point": "when measured", "extraction_method": "how value is read"},
        "assertion": {"predicate": "what is asserted", "failure_condition": "what meaningful failure means", "rationale": "why this measures the invariant"},
        "setup": ["required setup"],
        "timeout_seconds": 30,
    }
    return f"""You are a constrained trigger-plan generator in a controlled software-testing experiment.

The mechanism hypothesis is frozen. Do not revise, broaden, or replace it. Generate exactly {PLAN_COUNT} meaningfully different executable plans for that same hypothesis. Diversity must change a supported input boundary, state setup, environment, sequence, or public interface path; changing only a character is not diversity. Only use dimensions supported by the hypothesis and the visible buggy target context. Do not use fixed source, patches, issue text, hidden regression tests, evaluator verdicts, or benchmark metadata.

{refinement}

Return JSON only with exactly one top-level key, `plans`, whose value is a list of 1 to {PLAN_COUNT} plan objects. Every plan must contain exactly the fields and nested fields shown below. Actions are ordered. Use only these action types: create_input, set_environment, initialize_state, invoke, observe. Every plan must contain an invoke action followed by an observe action. The assertion must measure the observable at the stated measurement point and must not be a generic unconditional failure.

SCHEMA:
{json.dumps(schema, ensure_ascii=False, indent=2)}

Before emitting JSON, answer internally: (1) what exact state exists first, (2) what exact sequence activates the mechanism, (3) what runtime value makes it observable, (4) why the assertion measures the invariant, and (5) how it avoids unrelated failures. Do not include those answers outside the schema.

FROZEN HYPOTHESIS:
{json.dumps(visible, ensure_ascii=False, indent=2)}

TARGET CONTEXT (buggy checkout only):
{target_context}

STRUCTURED HISTORY ALREADY USED TO FORM THE HYPOTHESIS:
{json.dumps(history, ensure_ascii=False, indent=2)}

{feedback}
"""


def _base(record: dict[str, Any], iteration: int, arm: str) -> dict[str, Any]:
    return {
        "experiment": "experiment4", "iteration": iteration, "mode": "conditional", "arm": arm,
        "hypothesis_id": record["hypothesis_id"], "hypothesis": record["hypothesis"],
        "trigger": record.get("trigger", ""), "oracle": record.get("oracle", {}),
        "hypothesis_sha256": record["hypothesis_sha256"], "hypothesis_frozen": True,
        "generation_visible_files": record["generation_visible_files"],
    }


def generate_c1(record: dict[str, Any], client: DeepSeekClient, iteration: int, out_root: Path, test_root: Path, replicate: int = 1, arm: str = "C1") -> dict[str, Any]:
    started = time.time()
    result_record = _base(record, iteration, arm) | {"trigger_id": "direct" if replicate == 1 else f"direct-{replicate}", "trigger_type": "DIRECT", "replicate": replicate, "repair_attempts": 0}
    try:
        response = client.generate(hypothesis_prompt(record), max_tokens=MAX_TOKENS)
        parsed = parse_test_response(response.content)
        result_record.update(parsed, llm=response.log_record)
        if parsed["status"] == "TEST":
            test_id = f"{record['hypothesis_id']}-direct" if replicate == 1 else f"{record['hypothesis_id']}-direct-{replicate}"
            path = test_root / f"{_safe_name(test_id)}.py"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(parsed["test_code"] + "\n")
            result_record.update({"test_id": test_id, "test_path": str(path.relative_to(ROOT)), "test_sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    except Exception as exc:
        result_record.update({"status": "MODEL_ERROR", "error": str(exc)[:500], "llm": {"model": client.model, "request_count": client.request_count, "usage": {}}})
    result_record["wall_clock_seconds"] = round(time.time() - started, 3)
    _write_json(out_root / f"{_safe_name(record['hypothesis_id'])}__direct-{replicate}.json", result_record)
    return result_record


def generate_c2(record: dict[str, Any], client: DeepSeekClient, context: str, history: list[dict[str, Any]], iteration: int, out_root: Path, test_root: Path) -> list[dict[str, Any]]:
    base = _base(record, iteration, "C2")
    planner_attempts = []
    plans = None
    feedback = ""
    for attempt in range(MAX_REPAIRS + 1):
        started = time.time()
        try:
            response = client.generate(plan_prompt(record, context, history, iteration, feedback), max_tokens=MAX_TOKENS)
            try:
                plans = parse_plan_response(response.content, record["hypothesis_id"], context, limit=PLAN_COUNT)
                planner_attempts.append({"attempt": attempt, "status": "VALID", "llm": response.log_record, "wall_clock_seconds": round(time.time() - started, 3)})
                break
            except Exception as exc:
                error = str(exc)[:1000]
                planner_attempts.append({"attempt": attempt, "status": "INVALID", "error": error, "response": response.content, "llm": response.log_record, "wall_clock_seconds": round(time.time() - started, 3)})
                feedback = f"Your previous response failed deterministic validation with these errors: {error}. Repair only the JSON/schema/sequence/assertion alignment. Keep the frozen hypothesis unchanged. Return JSON only with exactly the required plans schema."
        except Exception as exc:
            error = str(exc)[:1000]
            planner_attempts.append({"attempt": attempt, "status": "MODEL_ERROR", "error": error, "wall_clock_seconds": round(time.time() - started, 3)})
            feedback = f"The previous planner call failed: {error}. Return the required JSON only."
    planner_record = base | {
        "status": "PLANS" if plans else "PLAN_INVALID",
        "planner_attempts": planner_attempts,
        "planner_repair_attempts": max(0, len(planner_attempts) - 1),
        "plans": plans or [],
        "planner_calls": len(planner_attempts),
    }
    _write_json(out_root / f"{_safe_name(record['hypothesis_id'])}__planner.json", planner_record)
    if not plans:
        return [planner_record]
    results = [planner_record]
    for index, plan in enumerate(plans, 1):
        trigger_id = f"plan-{index}"
        started = time.time()
        result_record = base | {"trigger_id": trigger_id, "trigger_type": "PLAN", "trigger_plan": plan, "repair_attempts": 0}
        try:
            response = client.generate(plan_test_prompt(record, plan, context, iteration), max_tokens=MAX_TOKENS)
            parsed = parse_test_response(response.content)
            if parsed["status"] == "TEST":
                parsed["test_code"] = validate_generated_test_code(parsed["test_code"])
            result_record.update(parsed, llm=response.log_record)
            if parsed["status"] == "TEST":
                test_id = f"{record['hypothesis_id']}-{trigger_id}"
                path = test_root / f"{_safe_name(test_id)}.py"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(parsed["test_code"] + "\n")
                result_record.update({"test_id": test_id, "test_path": str(path.relative_to(ROOT)), "test_sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        except Exception as exc:
            result_record.update({"status": "MODEL_ERROR", "error": str(exc)[:500], "llm": {"model": client.model, "request_count": client.request_count, "usage": {}}})
        result_record["wall_clock_seconds"] = round(time.time() - started, 3)
        _write_json(out_root / f"{_safe_name(record['hypothesis_id'])}__{trigger_id}.json", result_record)
        results.append(result_record)
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iteration", type=int, choices=[1, 2, 3], required=True)
    parser.add_argument("--arm", choices=["C1", "C1B", "C2", "both"], default="both")
    args = parser.parse_args()
    client = DeepSeekClient(model=MODEL, temperature=TEMPERATURE)
    context = TARGET_CONTEXT.read_text()
    history = json.loads(HISTORY.read_text())
    hypotheses = load_frozen_hypotheses()
    root = ROOT / "artifacts/experiment4" / f"iteration{args.iteration}"
    (root / "hypotheses").mkdir(parents=True, exist_ok=True)
    for record in hypotheses:
        _write_json(root / "hypotheses" / f"{record['hypothesis_id']}.json", record)
    if args.arm in {"C1", "both"}:
        for record in hypotheses:
            generate_c1(record, client, args.iteration, root / "C1", ROOT / "generated_tests/experiment4" / f"iteration{args.iteration}" / "C1", replicate=1, arm="C1")
    if args.arm == "C1B":
        for record in hypotheses:
            for replicate in range(1, PLAN_COUNT + 1):
                generate_c1(record, client, args.iteration, root / "C1_BUDGETED", ROOT / "generated_tests/experiment4" / f"iteration{args.iteration}" / "C1_BUDGETED", replicate=replicate, arm="C1_BUDGETED")
    if args.arm in {"C2", "both"}:
        for record in hypotheses:
            generate_c2(record, client, context, history, args.iteration, root / "C2", ROOT / "generated_tests/experiment4" / f"iteration{args.iteration}" / "C2")
    print(json.dumps({"iteration": args.iteration, "requests": client.request_count, "root": str(root.relative_to(ROOT))}))


if __name__ == "__main__":
    main()
