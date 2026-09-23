from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

try:
    from .experiment3_metrics import summarize_trigger_rows
except ImportError:
    from experiment3_metrics import summarize_trigger_rows


ROOT = Path(__file__).resolve().parents[1]


def read_rows() -> list[dict]:
    path = ROOT / "results/experiment3_results.csv"
    return list(csv.DictReader(path.open())) if path.exists() else []


def as_bool(value: str) -> bool:
    return str(value).lower() in {"true", "1", "yes"}


def main() -> None:
    rows = read_rows()
    status = {
        "natural": {"C1": "BLOCKED_MISSING_DEEPSEEK_API_KEY", "C2": "BLOCKED_MISSING_DEEPSEEK_API_KEY"},
        "conditional": {"C1": "REPLAYED_STORED_EXPERIMENT2_TESTS", "C2": "BLOCKED_MISSING_DEEPSEEK_API_KEY"},
        "model_generation_executed": False,
        "reason": "DEEPSEEK_API_KEY was absent from the environment and empty in .env",
    }
    (ROOT / "results/experiment3_run_status.json").write_text(json.dumps(status, indent=2) + "\n")
    lines = [
        "# Experiment 3 summary",
        "",
        "## Execution status",
        "",
        "New LLM generation did not run because `DEEPSEEK_API_KEY` was absent from the environment and empty in `.env`. The implementation therefore does not claim a completed C1/C2 comparison. Conditional C1 below is an offline replay of five previously stored mechanism-matched C tests, executed unchanged through the current evaluator.",
        "",
        "## Observed offline conditional C1 replay",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| hypotheses | {len({r['hypothesis_id'] for r in rows})} |",
        f"| executable tests | {sum(r['test_status'] == 'EXECUTABLE' for r in rows)} |",
        f"| mechanism-matched rows | {sum(r['mechanism_match'] == 'yes' for r in rows)} |",
        f"| verified F2P | {sum(as_bool(r['verified_f2p']) for r in rows)} |",
        f"| EXCEPTION_F2P | {sum(r['classification'] == 'EXCEPTION_F2P' for r in rows)} |",
        f"| F2F | {sum(r['classification'] == 'F2F' for r in rows)} |",
        f"| P2P | {sum(r['classification'] == 'P2P' for r in rows)} |",
        f"| activated buggy executions | {sum(r['activation'] == 'ACTIVATED' for r in rows)} |",
        "",
        "This replay reproduces stored Experiment 2 evidence and is not evidence that the new planner improves trigger construction. C2 has no generated candidates, so diversity yield, trigger-to-F2P improvement, and budget-normalized causal comparison are undefined.",
        "",
        "## Required comparison status",
        "",
        "| Mode | C1 | C2 | Comparison |",
        "|---|---|---|---|",
        "| 3A natural | blocked | blocked | not estimable |",
        "| 3B conditional | stored-test replay | blocked | not estimable |",
        "",
        "## Interpretation",
        "",
        "The available evidence supports only that the existing evaluator still recognizes the two previously observed exception-based F2P cases when their unchanged tests are replayed. It does not support any claim about trigger diversification. The single next action is to provide the required API credential, rerun the exact commands in the reviewer report, and then compare C1/C2 with the predeclared budget metrics.",
    ]
    (ROOT / "results/experiment3_summary.md").write_text("\n".join(lines))

    failure_lines = [
        "# Experiment 3 failure analysis",
        "",
        "No new C2 trigger candidates were generated because the model credential was unavailable. Therefore no new trigger-level failure taxonomy can be inferred. The five offline C1 replay rows are retained without filtering:",
        "",
        "| Hypothesis | Classification | Activation | Failure category |",
        "|---|---|---|---|",
    ]
    for row in rows:
        failure_lines.append(f"| {row['hypothesis_id']} | {row['classification']} | {row['activation']} | {row['failure_category']} |")
    failure_lines += [
        "",
        "The replay contains two valid exception-based F2P rows, one F2F row, and two P2P rows. These are unchanged prior tests and must not be attributed to the new intervention.",
        "",
        "No rows were discarded because of outcome. No thresholds or oracle rules were changed.",
    ]
    (ROOT / "results/experiment3_failure_analysis.md").write_text("\n".join(failure_lines) + "\n")

    budget = [
        "# Experiment 3 budget analysis",
        "",
        "## Planned budget",
        "",
        "C1 uses one direct test per frozen hypothesis. C2 uses one planner call plus up to four test-generation calls per frozen hypothesis. Every retained test is executed once on buggy and once on fixed. C2 therefore costs more execution and LLM budget by design; F2P counts must be normalized by hypotheses, executed tests, calls, tokens, and time.",
        "",
        "## Observed budget",
        "",
        "| Mode/arm | Hypotheses | Generated tests | Buggy/fixed pairs | LLM calls | Status |",
        "|---|---:|---:|---:|---:|---|",
        f"| conditional/C1 replay | {len({r['hypothesis_id'] for r in rows})} | {sum(r['test_status'] == 'EXECUTABLE' for r in rows)} | {2 * sum(r['test_status'] == 'EXECUTABLE' for r in rows)} | 0 new | completed replay |",
        "| natural/C1 | 0 | 0 | 0 | 0 | blocked |",
        "| natural/C2 | 0 | 0 | 0 | 0 | blocked |",
        "| conditional/C2 | 0 | 0 | 0 | 0 | blocked |",
        "",
        "Because C2 did not run, executions per verified F2P for the new intervention, calls/tokens per verified F2P, time to first new F2P, and budget-normalized C1/C2 differences are undefined. The replay's two F2P cases are historical baseline evidence only.",
    ]
    (ROOT / "results/experiment3_budget_analysis.md").write_text("\n".join(budget))

    reviewer = [
        "# Experiment 3 reviewer report",
        "",
        "## Scope and intervention",
        "",
        "The approved intervention is a generic structured trigger planner with N=4 candidates after a frozen structured-history hypothesis. The code preserves Experiment 2 and reuses the exception-aware evaluator.",
        "",
        "## Reproducibility commands",
        "",
        "```bash",
        "python3 scripts/verify_harness.py",
        "python3 scripts/prepare_experiment3.py --limit 5",
        "set -a; source .env; set +a; python3 scripts/run_experiment3.py --mode natural --arm both --attempts 5",
        "set -a; source .env; set +a; python3 scripts/run_experiment3.py --mode conditional --arm both --attempts 5",
        "python3 scripts/evaluate_experiment3.py --mode all",
        "python3 scripts/write_experiment3_reports.py",
        "```",
        "",
        "The two generation commands require a non-empty `DEEPSEEK_API_KEY`; it is read from the environment and never printed or stored.",
        "",
        "## Review conclusion",
        "",
        "The implementation is present and the offline replay is verified, but the primary C1/C2 experiment is incomplete. It would be methodologically invalid to report the replayed C1 F2P count as a trigger-planner improvement or to invent C2 outcomes. Once credentials are available, rerun the commands above; the generated artifacts and CSV schema already preserve frozen hypothesis hashes, trigger plans, test hashes, execution logs, and cost fields.",
    ]
    (ROOT / "results/experiment3_reviewer_report.md").write_text("\n".join(reviewer) + "\n")


if __name__ == "__main__":
    main()
