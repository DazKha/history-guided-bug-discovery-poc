# Experiment 5B — conditional planner replication

The evaluator-only selector found `0/10` eligible C hypotheses: no C artifact had both a supported pre-execution oracle and a mechanism match for Tornado:1. The prescribed maximum sample of five therefore could not be formed.

Per the frozen protocol, no hypothesis was rewritten or topped up, and no C1 direct or C2 Experiment 4 planner calls were made.

| Arm | Frozen hypotheses | Candidate slots | LLM calls | F2P | Hypotheses with F2P | Status |
|---|---:|---:|---:|---:|---:|---|
| C1 budget-matched direct | 0 | 0 | 0 | 0 | 0 | underpowered / not run |
| C2 frozen Experiment 4 planner | 0 | 0 | 0 | 0 | 0 | underpowered / not run |

The empty `results/experiment5_conditional.csv` is intentional and contains the fixed conditional schema header. `data/experiment5_selected_hypotheses.json` and `artifacts/experiment5/conditional_run_status.json` preserve the selection and stop decision.
