# Experiment 3 reviewer report

## Scope and intervention

The approved intervention is a generic structured trigger planner with N=4 candidates after a frozen structured-history hypothesis. The code preserves Experiment 2 and reuses the exception-aware evaluator.

## Reproducibility commands

```bash
python3 scripts/verify_harness.py
python3 scripts/prepare_experiment3.py --limit 5
set -a; source .env; set +a; python3 scripts/run_experiment3.py --mode natural --arm both --attempts 5
set -a; source .env; set +a; python3 scripts/run_experiment3.py --mode conditional --arm both --attempts 5
python3 scripts/evaluate_experiment3.py --mode all
python3 scripts/write_experiment3_reports.py
```

The two generation commands require a non-empty `DEEPSEEK_API_KEY`; it is read from the environment and never printed or stored.

## Review conclusion

The implementation is present and the offline replay is verified, but the primary C1/C2 experiment is incomplete. It would be methodologically invalid to report the replayed C1 F2P count as a trigger-planner improvement or to invent C2 outcomes. Once credentials are available, rerun the commands above; the generated artifacts and CSV schema already preserve frozen hypothesis hashes, trigger plans, test hashes, execution logs, and cost fields.
