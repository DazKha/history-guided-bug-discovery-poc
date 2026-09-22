from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def rows():
    return list(csv.DictReader((ROOT / "results/experiment2_results.csv").open()))


def summary():
    return list(csv.DictReader((ROOT / "results/experiment2_summary.csv").open()))


def table(rows_: list[dict]) -> str:
    lines = ["| Attempt | Status | Outcome | Mechanism match | Target oracle | Failure layer |", "|---:|---|---|---|---|---|"]
    for row in rows_:
        lines.append(f"| {row['attempt']} | {row['status']} | {row['outcome']} | {row['hypothesis_matches_true_failure_mechanism']} | {row['oracle_supported_by_target_evidence']} | {row['failure_layer'] or '—'} |")
    return "\n".join(lines)


def main() -> None:
    result_rows = rows()
    sums = summary()
    manifest = json.loads((ROOT / "data/target_leakage_manifest.json").read_text())
    candidates = json.loads((ROOT / "data/transfer_case_candidates.json").read_text())
    chosen = candidates["chosen_candidate"]
    lines = [
        "# Experiment 2 failure analysis",
        "",
        "The final run used five attempts per condition. Classification is based on unchanged generated tests executed on the verified buggy and fixed checkouts. `F2P` requires an assertion-level semantic failure on buggy and a pass on fixed; an unhandled target exception is not counted as a meaningful assertion failure.",
        "",
        f"Chosen target: `{manifest['target_id']}`. Historical subset: `{', '.join(manifest['selected_history_ids'])}`.",
        "",
    ]
    for row in sums:
        lines += [
            f"## {row['condition']} — {row['condition_name']}",
            "",
            f"Attempts={row['attempts']}; tests={row['executable_tests']}; meaningful buggy failures={row['meaningful_failures_on_buggy']}; F2P={row['F2P']}; F2F={row['F2F']}; P2P={row['P2P']}; P2F={row['P2F']}; mechanical={row['MECHANICAL_FAILURE']}; model/no-support={row['NO_SUPPORTED_HYPOTHESIS']}/{int(row['attempts']) - int(row['executable_tests'])}; mechanism-match={row['mechanism_match_yes']}; target-oracle-supported={row['oracle_supported_yes']}; repairs={row['repair_attempts']}; LLM calls={row['llm_calls']}.",
            "",
            table([r for r in result_rows if r["condition"] == row["condition"]]),
            "",
        ]
    lines += [
        "## Layer interpretation",
        "",
        "- A: all five executable tests were P2P; the model explored plausible state/tracing hypotheses but none matched the hidden encoding mechanism.",
        "- B: four tests were generated and one attempt returned no JSON. The raw evidence did not produce an encoding-mechanism match; executable tests were P2P.",
        "- C: two attempts returned no usable JSON, one weak-history hypothesis was P2P, one mechanism-matching source-decoding test was P2P, and one mechanism-matching test was F2F because its oracle failed on both revisions. This is transfer signal without verified discovery.",
        "- The first exploratory generation pass is preserved under `artifacts/experiment2_llm_run1/` and `generated_tests/experiment2_run1/`. It produced two exception-level buggy failures with fixed passes for encoding hypotheses, but those were deliberately excluded from F2P because the tests did not turn the expected no-error property into an assertion.",
        "",
        "No generated test in the final strict run achieved F2P. This is a negative result about this small feasibility run, not evidence that the target mechanism is absent: the evaluator-only target truth and the exception trace show the mechanism is real, while test/oracle construction remained the bottleneck.",
    ]
    (ROOT / "results/experiment2_failure_analysis.md").write_text("\n".join(lines) + "\n")

    case = f"""# Experiment 2 case study

## Selected transfer case

The evaluator retrospectively selected `{manifest['target_id']}` and the two historical units `{', '.join(manifest['selected_history_ids'])}`. The strongest relationship is `cookiecutter:1`: its fix changes implicit `open(...)` decoding to explicit UTF-8 and adds a non-ASCII regression fixture. `PySnooper:3` is intentionally weaker: it is a public file-output path bug but its historical mechanism is a path-variable mismatch, not encoding. The subset was selected by mechanism/trigger/invariant compatibility, not lexical similarity.

This is a retrospectively selected transfer-feasibility experiment. It evaluates whether the mechanism can transfer when suitable history is available. It does not evaluate autonomous retrieval quality.

## Leakage boundary

Generation read only `{manifest['agent_visible']['target_context']}`, plus the raw or structured history file for B/C. The evaluator-only truth is `{manifest['evaluator_only']['truth_file']}`; the fixed checkout and hidden regression are not read by `scripts/run_experiment2.py`.

## Representative structured attempt

Final C attempt 5 (`generated_tests/experiment2/PySnooper_1/C_attempt_5.py`) correctly identified the target-side source-decoding region and marked `cookiecutter:1` as supported. It generated a UTF-8 source-file probe with a meaningful assertion. The exact same test failed on both buggy and fixed revisions (`F2F`): the test re-decorated a module function in a way that did not isolate the fixed source-decoding behavior, and its expected source-line assertion was not satisfied on either revision. This is an oracle/test-construction failure, not F2P.

## Important exploratory signal

Before tightening the test contract, run-1 C attempt 1 generated a direct non-ASCII file-output probe grounded in `FileWriter.write`. The unchanged test failed on the buggy checkout with `UnicodeEncodeError` at `pysnooper/tracer.py:134` and passed on the fixed checkout. That is a strong exception-level mechanism signal, but it was not counted as F2P because the test let the expected target exception escape rather than failing at an intended assertion. The run-1 artifact and logs remain available for review; the final run required assertion-level handling equally across A/B/C.

## Conclusion from this case

Structured applicability clearly helped the model select the right mechanism more often than A or B (`2/5` mechanism-match labels for C versus `0/5` for A and `0/4` for B executable attempts), but the final objective discovery count was `0/5` F2P for every condition. The evidence supports “useful transfer signal with unresolved executable-oracle reliability,” not a positive discovery claim.
"""
    (ROOT / "results/experiment2_case_study.md").write_text(case)

    comparison = """# Experiment 2 comparison with Experiment 1

| Experiment | Condition | Attempts | Tests | F2P | P2P | F2F | Mechanical | Abstentions/model errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Exp1 | A target-only | 5 | 4 | 0 | 3 | 0 | 1 | 1 no-support |
| Exp1 | B raw history | 5 | 0 | 0 | 0 | 0 | 0 | 5 no-support |
| Exp1 | C structured | 5 | 0 | 0 | 0 | 0 | 0 | 5 no-support |
| Exp2 final | A target-only | 5 | 5 | 0 | 5 | 0 | 0 | 0 |
| Exp2 final | B raw history | 5 | 4 | 0 | 4 | 0 | 0 | 1 model error |
| Exp2 final | C structured | 5 | 3 | 0 | 2 | 1 | 0 | 2 model errors |

Exp1 was inconclusive because the raw baseline did not receive the raw fix diff containing the strongest transferable evidence, the common prompt applied C-style abstention to B, the structured fields were generic, and target runtime locale facts were omitted from the context.

Exp2 controlled those confounds: it used the same small historical subset for B/C, included the actual raw diffs for B, used concise mechanism-centered units for C, exposed only ordinary target source/docs/tests plus runtime facts, and applied the applicability gate only to C. The final strict run still produced no assertion-level F2P result. C generated the most mechanism-aligned hypotheses, but one was P2P and one F2F; A and B generated no mechanism-aligned hypothesis in this sample.

The preserved exploratory run contains an exception-level buggy/fixed split for a C encoding test. It is disclosed but not promoted to F2P because it did not meet the predeclared assertion-level criterion. The follow-up conclusion is therefore: Exp2 demonstrates improved mechanism targeting and a real near-transfer signal, but not verified positive discovery superiority.
"""
    (ROOT / "results/experiment2_comparison_with_experiment1.md").write_text(comparison)


if __name__ == "__main__":
    main()
