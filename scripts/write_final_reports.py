from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROWS = list(csv.DictReader((ROOT / "results/experiment2_re_evaluated.csv").open()))


def count(rows: list[dict], field: str, value: str) -> int:
    return sum(row[field] == value for row in rows)


def total_verified(rows: list[dict]) -> int:
    return sum(row["verified_f2p"] == "True" for row in rows)


def summary_row(condition: str) -> dict:
    subset = [row for row in ROWS if row["condition"] == condition]
    return {
        "condition": condition,
        "attempts": len(subset),
        "mechanism_matches": count(subset, "hypothesis_matches_true_failure_mechanism", "yes"),
        "supported_hypotheses": count(subset, "oracle_status", "SUPPORTED_ORACLE"),
        "executable_tests": sum(row["status"] == "TEST" and bool(row["test_path"]) for row in subset),
        "assertion_f2p": count(subset, "classification", "ASSERTION_F2P"),
        "exception_f2p": count(subset, "classification", "EXCEPTION_F2P"),
        "total_verified_f2p": total_verified(subset),
        "p2p": count(subset, "classification", "P2P"),
        "f2f": count(subset, "classification", "F2F"),
        "mechanical": count(subset, "classification", "MECHANICAL_FAILURE"),
        "unsupported_oracles": count(subset, "classification", "UNSUPPORTED_ORACLE"),
        "no_support": sum(row["classification"] in {"MODEL_ERROR", "NO_SUPPORTED_HYPOTHESIS"} for row in subset),
        "false_unverified": sum(row["verified_f2p"] != "True" for row in subset),
        "llm_calls": sum(int(row["llm_calls"] or 0) for row in subset),
        "prompt_tokens": sum(int(row["prompt_tokens"] or 0) for row in subset),
        "completion_tokens": sum(int(row["completion_tokens"] or 0) for row in subset),
        "wall_clock": round(sum(float(row["wall_clock_seconds"] or 0) for row in subset), 3),
    }


def md_table(rows: list[dict]) -> str:
    header = "| Condition | Attempts | Mechanism Matches | Supported Hypotheses | Executable Tests | Assertion F2P | Exception F2P | Total Verified F2P | P2P | F2F | Mechanical | Unsupported Oracles | No-Supported/Model | False/Unverified | LLM Calls | Tokens (prompt/completion) | Wall Clock (s) |"
    divider = "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    lines = [header, divider]
    for row in rows:
        lines.append(f"| {row['condition']} | {row['attempts']} | {row['mechanism_matches']} | {row['supported_hypotheses']} | {row['executable_tests']} | {row['assertion_f2p']} | {row['exception_f2p']} | {row['total_verified_f2p']} | {row['p2p']} | {row['f2f']} | {row['mechanical']} | {row['unsupported_oracles']} | {row['no_support']} | {row['false_unverified']} | {row['llm_calls']} | {row['prompt_tokens']}/{row['completion_tokens']} | {row['wall_clock']} |")
    return "\n".join(lines)


def main() -> None:
    aggregate = [summary_row(condition) for condition in ["A", "B", "C"]]
    batches = []
    for label in ["exploratory", "final", "loop1"]:
        batch_rows = [row for row in ROWS if row["run_label"] == label]
        if batch_rows:
            batches.append((label, [summary_row_for_rows(condition, batch_rows) for condition in ["A", "B", "C"]]))
    lines = [
        "# Final failure analysis",
        "",
        "The corrected criterion is: `verified_f2p = same unchanged test on buggy and fixed AND buggy has a meaningful semantic failure AND fixed passes AND oracle was supported before execution`. Meaningful semantic failure is either an assertion failure or a target exception that violates that pre-execution oracle. Setup/environment exceptions remain mechanical.",
        "",
        "## Aggregate Experiment 2 evidence",
        "",
        md_table(aggregate),
        "",
        "The aggregate includes 15 attempts per condition: the preserved exploratory batch, the later strict batch, and one additional uniform looped batch. The only verified F2P results are two `EXCEPTION_F2P` cases in exploratory C. There are no assertion F2P results.",
        "",
    ]
    for label, batch in batches:
        lines += [f"## Batch: {label}", "", md_table(batch), ""]
    lines += [
        "## Localized failure analysis",
        "",
        "- A generated plausible target behavior but did not match the locale-dependent encoding mechanism in any batch; its executable tests were P2P or model errors.",
        "- B occasionally picked up adjacent file-output or encoding language, but did not produce a verified F2P; raw history remained distracted by unrelated state/path hypotheses.",
        "- C identified the true encoding mechanism repeatedly (9/15 aggregate mechanism-match labels). Two exploratory C tests directly exercised the public path-output API and produced target `UnicodeEncodeError` on buggy with fixed passes; these are valid exception-based F2P under the corrected rule.",
        "- Later strict and looped C attempts did not reproduce F2P: the strict batch had two model errors, two P2P tests, and one F2F; the looped batch had four P2P tests and one F2F despite three mechanism matches. This localizes the remaining instability to trigger/test construction, not historical mechanism identification.",
        "- No tests were edited between buggy and fixed execution. The exploratory oracle and hypothesis are taken from the stored model artifact created before execution; the evaluator does not rewrite them after observing outcomes.",
        "",
        "## Conclusion",
        "",
        "In this retrospectively selected transfer-feasibility case, structured historical knowledge identified the correct failure mechanism and produced verified executable evidence distinguishing the buggy and fixed revisions. The evidence does not prove the architecture: the two valid F2P cases occur in one exploratory batch, later attempts did not reproduce them, and A/B did not produce valid F2P. The stable conclusion is that structured history improves search direction here, while robust trigger construction remains the bottleneck.",
    ]
    (ROOT / "results/failure_analysis_final.md").write_text("\n".join(lines) + "\n")


def summary_row_for_rows(condition: str, rows: list[dict]) -> dict:
    subset = [row for row in rows if row["condition"] == condition]
    # Reuse the aggregate schema without mutating global rows.
    return {
        "condition": condition,
        "attempts": len(subset),
        "mechanism_matches": count(subset, "hypothesis_matches_true_failure_mechanism", "yes"),
        "supported_hypotheses": count(subset, "oracle_status", "SUPPORTED_ORACLE"),
        "executable_tests": sum(row["status"] == "TEST" and bool(row["test_path"]) for row in subset),
        "assertion_f2p": count(subset, "classification", "ASSERTION_F2P"),
        "exception_f2p": count(subset, "classification", "EXCEPTION_F2P"),
        "total_verified_f2p": total_verified(subset),
        "p2p": count(subset, "classification", "P2P"),
        "f2f": count(subset, "classification", "F2F"),
        "mechanical": count(subset, "classification", "MECHANICAL_FAILURE"),
        "unsupported_oracles": count(subset, "classification", "UNSUPPORTED_ORACLE"),
        "no_support": sum(row["classification"] in {"MODEL_ERROR", "NO_SUPPORTED_HYPOTHESIS"} for row in subset),
        "false_unverified": sum(row["verified_f2p"] != "True" for row in subset),
        "llm_calls": sum(int(row["llm_calls"] or 0) for row in subset),
        "prompt_tokens": sum(int(row["prompt_tokens"] or 0) for row in subset),
        "completion_tokens": sum(int(row["completion_tokens"] or 0) for row in subset),
        "wall_clock": round(sum(float(row["wall_clock_seconds"] or 0) for row in subset), 3),
    }


if __name__ == "__main__":
    main()
