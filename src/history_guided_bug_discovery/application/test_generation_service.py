from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from ..config.models import RunConfig
from ..domain.enums import Arm
from ..domain.models import FrozenHypothesis, TestArtifact, TriggerPlan
from ..ports.llm import GenerationRequest, GenerationResponse, LLMProvider
from .prompts import direct_test_v1, plan_to_test_compact_v1

FORBIDDEN_TERMS = (
    "assert false", "pytest.fail", "git show", "git diff", "bug_patch.txt",
    "test_chinese.py", "vendor/bugsinpy", "harness-pysnooper-fixed",
    "fixed checkout", "fixed revision", ".git/objects", "hidden test",
)


def preflight_test_source(source: str) -> str:
    try:
        tree = ast.parse(source)
        compile(tree, "<generated-test>", "exec")
    except (SyntaxError, ValueError, TypeError) as exc:
        raise ValueError(f"syntax or compilation failure: {exc}") from exc
    lowered = source.lower()
    if any(term in lowered for term in FORBIDDEN_TERMS):
        raise ValueError("forbidden construction or hidden-target access")
    if not any(isinstance(node, ast.Assert) for node in ast.walk(tree)):
        raise ValueError("generated test contains no meaningful assertion")
    if any(isinstance(node, ast.Assert) and isinstance(node.test, ast.Constant) and node.test.value is False for node in ast.walk(tree)):
        raise ValueError("generated test contains unconditional assert False")
    if re.search(r"\bsubprocess\.(run|Popen|call|check_call|check_output)\b", source) and "shell=True" in lowered:
        raise ValueError("forbidden shell inspection construction")
    return source


def parse_test_response(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = text.replace("```json", "", 1).replace("```", "").strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("test response did not contain a JSON object")
    obj = json.loads(text[start:end + 1])
    status = str(obj.get("status", "")).upper()
    if status in {"HYPOTHESIS", "SUPPORTED", "TEST"}:
        status = "TEST"
    elif status in {"NO_SUPPORTED_HYPOTHESIS", "NO_HYPOTHESIS", "ABSTAIN"}:
        status = "NO_SUPPORTED_HYPOTHESIS"
    else:
        raise ValueError(f"unsupported test status: {status}")
    code = str(obj.get("test_code") or "")
    if status == "TEST" and not code:
        raise ValueError("test output is empty")
    return {"status": status, "test_code": code}


@dataclass(frozen=True)
class GeneratedTestResult:
    status: str
    artifact: TestArtifact | None
    response: GenerationResponse | None
    prompt_hash: str
    error: str = ""


class TestGenerationService:
    def __init__(self, provider: LLMProvider, config: RunConfig):
        self.provider = provider
        self.config = config

    def generate(self, hypothesis: FrozenHypothesis, arm: Arm, artifact_id: str, plan: TriggerPlan | None = None, target_context: str = "") -> GeneratedTestResult:
        strategy = "direct_test_v1" if plan is None else "plan_to_test_compact_v1"
        prompt = direct_test_v1(hypothesis) if plan is None else plan_to_test_compact_v1(hypothesis, plan.plan, target_context)
        request = GenerationRequest(self.config.run_id, artifact_id, strategy, prompt, self.config.model.name, self.config.model.temperature, self.config.model.max_output_tokens, self.config.model.timeout_seconds, self.config.model.response_format, self.config.model.thinking)
        response = None
        try:
            response = self.provider.generate(request)
            parsed = parse_test_response(response.content)
            if parsed["status"] != "TEST":
                return GeneratedTestResult(parsed["status"], None, response, request.prompt_hash)
            code = preflight_test_source(parsed["test_code"])
            artifact = TestArtifact.create(self.config.run_id, artifact_id, hypothesis.hypothesis_id, arm, code, request.prompt_hash, hypothesis.generation_visible_files, plan.plan_id if plan else None, strategy, response.log_record.get("model", request.model), response.usage)
            return GeneratedTestResult("TEST", artifact, response, request.prompt_hash)
        except Exception as exc:
            return GeneratedTestResult("MODEL_OUTPUT_FAILURE", None, None, request.prompt_hash, str(exc)[:500])
