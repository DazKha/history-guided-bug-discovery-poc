# Experiment 3 reviewer report

## Scope and intervention

The approved intervention is a generic structured trigger planner with N=4 candidates after a frozen structured-history hypothesis. The code preserves Experiment 2 and reuses the exception-aware evaluator.

## Reproducibility commands

```bash
python3 scripts/verify_harness.py
python3 scripts/prepare_experiment3.py --limit 5
export DEEPSEEK_API_KEY='set this in the shell; do not print or commit it'
python3 scripts/run_experiment3.py --mode natural --arm both --attempts 5 --run-label live2
python3 scripts/run_experiment3.py --mode conditional --arm both --attempts 5 --run-label live1
python3 scripts/run_experiment3.py --mode conditional --arm C2 --attempts 5 --run-label live2 --retry-failed-from live1
python3 scripts/run_experiment3.py --mode conditional --arm C2 --attempts 5 --run-label live3 --retry-failed-from live2
python3 scripts/evaluate_experiment3.py --mode all --natural-run-label live2 --conditional-run-label live1,live2,live3
```

The two generation commands require a non-empty `DEEPSEEK_API_KEY`; it is read from the environment and never printed or stored.

## Review conclusion

The primary conditional comparison ran. C2 found 3 F2P in 8 executed trigger-tests versus C1’s 2 F2P in 5 direct tests, but C2 used 20 LLM calls versus 5 and 8 versus 5 execution pairs. After normalization, C2 did not improve F2P per hypothesis or per executed test. Three of five hypotheses also failed to produce valid planner output after two bounded repairs. Natural 3A produced no executable tests. The strongest supported conclusion is that this planner configuration adds search breadth but does not yet improve trigger quality.
