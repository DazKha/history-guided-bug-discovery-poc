from __future__ import annotations

from pathlib import Path

from .aggregate import AggregateSummary


def render_markdown(summary: AggregateSummary) -> str:
    data = summary.to_dict()
    lines = [f"# Discovery run summary: {summary.arm}", "", "| Metric | Value |", "|---|---:|"]
    for key in ("candidate_slots", "generated_test_artifacts", "executable_tests", "meaningful_semantic_tests", "f2p", "f2f", "p2p", "p2f", "mechanical_failures", "model_output_failures", "f2p_hypotheses", "total_hypotheses", "valid_plan_hypotheses", "repair_successes", "llm_calls", "prompt_tokens", "completion_tokens", "total_tokens", "f2p_per_slot", "f2p_per_generated_artifact", "f2p_hypothesis_rate", "mechanical_failure_rate"):
        lines.append(f"| {key} | {data[key]} |")
    return "\n".join(lines) + "\n"


def write_markdown(summary: AggregateSummary, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown(summary), encoding="utf-8")
    return output
