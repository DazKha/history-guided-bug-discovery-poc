from __future__ import annotations

from dataclasses import dataclass, field
import csv
import json
from pathlib import Path
from typing import Any

from ..domain.enums import Arm


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


@dataclass
class AggregateSummary:
    arm: str
    candidate_slots: int = 0
    generated_test_artifacts: int = 0
    executable_tests: int = 0
    meaningful_semantic_tests: int = 0
    f2p: int = 0
    f2f: int = 0
    p2p: int = 0
    p2f: int = 0
    mechanical_failures: int = 0
    model_output_failures: int = 0
    no_supported_hypothesis: int = 0
    f2p_hypotheses: int = 0
    total_hypotheses: int = 0
    planner_attempts: int = 0
    valid_plan_hypotheses: int = 0
    repair_successes: int = 0
    llm_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @property
    def candidate_outcome_total(self) -> int:
        return self.f2p + self.f2f + self.p2p + self.p2f + self.mechanical_failures + self.model_output_failures + self.no_supported_hypothesis

    @property
    def f2p_per_slot(self) -> float:
        return self.f2p / self.candidate_slots if self.candidate_slots else 0.0

    @property
    def f2p_per_generated_artifact(self) -> float:
        return self.f2p / self.generated_test_artifacts if self.generated_test_artifacts else 0.0

    @property
    def f2p_hypothesis_rate(self) -> float:
        return self.f2p_hypotheses / self.total_hypotheses if self.total_hypotheses else 0.0

    @property
    def mechanical_failure_rate(self) -> float:
        return self.mechanical_failures / self.candidate_slots if self.candidate_slots else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {"arm": self.arm, "candidate_slots": self.candidate_slots, "generated_test_artifacts": self.generated_test_artifacts, "executable_tests": self.executable_tests, "meaningful_semantic_tests": self.meaningful_semantic_tests, "f2p": self.f2p, "f2f": self.f2f, "p2p": self.p2p, "p2f": self.p2f, "mechanical_failures": self.mechanical_failures, "model_output_failures": self.model_output_failures, "no_supported_hypothesis": self.no_supported_hypothesis, "f2p_hypotheses": self.f2p_hypotheses, "total_hypotheses": self.total_hypotheses, "planner_attempts": self.planner_attempts, "valid_plan_hypotheses": self.valid_plan_hypotheses, "repair_successes": self.repair_successes, "llm_calls": self.llm_calls, "prompt_tokens": self.prompt_tokens, "completion_tokens": self.completion_tokens, "total_tokens": self.total_tokens, "f2p_per_slot": self.f2p_per_slot, "f2p_per_generated_artifact": self.f2p_per_generated_artifact, "f2p_hypothesis_rate": self.f2p_hypothesis_rate, "mechanical_failure_rate": self.mechanical_failure_rate, "candidate_outcome_total": self.candidate_outcome_total, "metadata": self.metadata}


def aggregate_rows(rows: list[dict[str, Any]], arm: Arm | str) -> AggregateSummary:
    arm_value = arm.value if isinstance(arm, Arm) else str(arm)
    candidate_rows = [row for row in rows if row.get("stage", "TEST") == "TEST"]
    planner_rows = [row for row in rows if row.get("stage") == "PLANNER"]
    f2p_values = {"F2P", "ASSERTION_F2P", "EXCEPTION_F2P"}
    summary = AggregateSummary(arm_value)
    summary.candidate_slots = len(candidate_rows)
    summary.generated_test_artifacts = sum(row.get("test_status") == "EXECUTABLE" or bool(row.get("test_path")) for row in candidate_rows)
    summary.executable_tests = summary.generated_test_artifacts
    summary.meaningful_semantic_tests = sum(row.get("classification") in f2p_values | {"F2F", "P2P", "P2F"} for row in candidate_rows)
    summary.f2p = sum(row.get("classification") in f2p_values or str(row.get("verified_f2p", "")).lower() == "true" for row in candidate_rows)
    summary.f2f = sum(row.get("classification") == "F2F" for row in candidate_rows)
    summary.p2p = sum(row.get("classification") == "P2P" for row in candidate_rows)
    summary.p2f = sum(row.get("classification") == "P2F" for row in candidate_rows)
    summary.mechanical_failures = sum(row.get("classification") == "MECHANICAL_FAILURE" for row in candidate_rows)
    summary.model_output_failures = sum(row.get("classification") == "MODEL_ERROR" or row.get("test_status") == "MODEL_OUTPUT_FAILURE" for row in candidate_rows)
    summary.no_supported_hypothesis = sum(row.get("classification") == "NO_SUPPORTED_HYPOTHESIS" for row in candidate_rows)
    f2p_hypotheses = {row.get("hypothesis_id") for row in candidate_rows if row.get("classification") in f2p_values or str(row.get("verified_f2p", "")).lower() == "true"}
    hypotheses = {row.get("hypothesis_id") for row in rows if row.get("hypothesis_id")}
    summary.f2p_hypotheses = len(f2p_hypotheses - {None})
    summary.total_hypotheses = len(hypotheses)
    summary.planner_attempts = len(planner_rows)
    summary.valid_plan_hypotheses = len({row.get("hypothesis_id") for row in planner_rows if row.get("classification") == "PLAN_VALID"})
    summary.repair_successes = len({row.get("hypothesis_id") for row in planner_rows if row.get("classification") == "PLAN_VALID" and _int(row.get("planner_attempt_index")) > 0})
    summary.llm_calls = sum(_int(row.get("llm_calls")) for row in rows)
    summary.prompt_tokens = sum(_int(row.get("prompt_tokens")) for row in rows)
    summary.completion_tokens = sum(_int(row.get("completion_tokens")) for row in rows)
    return summary


def validate_consistency(summary: AggregateSummary) -> None:
    if summary.candidate_outcome_total != summary.candidate_slots:
        raise ValueError(f"candidate outcome totals {summary.candidate_outcome_total} do not equal candidate slots {summary.candidate_slots}")
    if summary.f2p_hypotheses > summary.total_hypotheses:
        raise ValueError("F2P hypotheses cannot exceed total hypotheses")
    if summary.generated_test_artifacts + summary.model_output_failures + summary.no_supported_hypothesis != summary.candidate_slots:
        raise ValueError("generated tests plus model-output/no-support failures do not equal candidate slots")


def validate_report_files(json_path: str | Path, csv_path: str | Path, markdown_path: str | Path) -> bool:
    json_data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    with Path(csv_path).open(newline="", encoding="utf-8") as handle:
        csv_data = next(csv.DictReader(handle))
    markdown_lines = Path(markdown_path).read_text(encoding="utf-8").splitlines()
    markdown_data = {}
    for line in markdown_lines:
        if line.startswith("|") and line.count("|") >= 3:
            parts = [part.strip() for part in line.strip("|").split("|")]
            if len(parts) == 2 and parts[0] not in {"Metric", "---"}:
                markdown_data[parts[0]] = parts[1]
    for key, value in json_data.items():
        if key == "metadata":
            continue
        if str(csv_data.get(key)) != str(value):
            raise ValueError(f"CSV disagrees with JSON for {key}")
        if key in markdown_data and markdown_data[key] != str(value):
            raise ValueError(f"Markdown disagrees with JSON for {key}")
    return True
