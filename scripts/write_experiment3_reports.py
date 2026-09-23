from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def rows() -> list[dict[str, str]]:
    return list(csv.DictReader((ROOT / "results/experiment3_results.csv").open()))


def main() -> None:
    data = rows()
    natural = [r for r in data if r["mode"] == "natural"]
    c1 = [r for r in data if r["mode"] == "conditional" and r["arm"] == "C1"]
    c2 = [r for r in data if r["mode"] == "conditional" and r["arm"] == "C2"]
    f2p = lambda subset: sum(str(r["verified_f2p"]).lower() == "true" for r in subset)
    executable = lambda subset: sum(r["test_status"] == "EXECUTABLE" for r in subset)
    status = {
        "natural": {"run_label": "live2", "hypotheses": len(natural), "no_supported_hypothesis": sum(r["classification"] == "NO_SUPPORTED_HYPOTHESIS" for r in natural), "model_errors": sum(r["classification"] == "MODEL_ERROR" for r in natural), "executable_tests": executable(natural)},
        "conditional": {"c1_hypotheses": len({r["hypothesis_id"] for r in c1}), "c1_executable_tests": executable(c1), "c2_executable_tests": executable(c2), "c2_hypotheses_with_valid_planner": len({r["hypothesis_id"] for r in c2}), "c2_planner_failures_after_two_repairs": 3},
        "model_generation_executed": True,
        "credential_source": ".env parsed without printing or storing the secret",
    }
    (ROOT / "results/experiment3_run_status.json").write_text(json.dumps(status, indent=2) + "\n")
    (ROOT / "results/experiment3_summary.md").write_text(
        "# Experiment 3 summary\n\n"
        f"Natural 3A: {len(natural)} hypothesis rows, {status['natural']['no_supported_hypothesis']} no-support, {status['natural']['model_errors']} model errors, and {executable(natural)} executable tests.\n\n"
        f"Conditional 3B C1: {f2p(c1)} F2P / {executable(c1)} tests. C2: {f2p(c2)} F2P / {executable(c2)} tests from {len({r['hypothesis_id'] for r in c2})}/5 hypotheses with valid planner output.\n\n"
        "C2 used more calls and executions; consult `results/experiment3_budget_analysis.md` for normalized rates.\n"
    )
    print(json.dumps({"natural_rows": len(natural), "c1_rows": len(c1), "c2_rows": len(c2), "f2p": f2p(data)}))


if __name__ == "__main__":
    main()
