# Experiment 5 reviewer report

## Verdict

This is a valid negative second-target replication for the end-to-end mechanism question, but the conditional planner question is underpowered and not estimable.

## Controls audited

- Target, buggy/fixed revisions, model (`deepseek-flash`), temperature (`0.2`), token cap (`2200`), attempt count, target context, analogue set, oracle policy, and evaluator semantics were frozen before generation.
- Generation saw only the buggy target context and the selected raw or structured historical representation for its condition.
- The target issue, patch, fixed checkout, hidden regression test, changed-file metadata, ground-truth mechanism, and evaluator outcomes were not passed to generation.
- The same selected analogue set (`PySnooper:3`, `cookiecutter:1`) was used for B and C; B received raw evidence and C received the existing structured representation.
- Every generated response, prompt, test, hash, token record, and buggy/fixed log was preserved.
- The Experiment 4 correction was limited to markdown summaries and an append-only note; raw Experiment 4 CSV and execution artifacts were not edited.

## Findings

1. The Tornado buggy/fixed harness is reproducible: the independent public-API probe fails only on buggy and passes on fixed.
2. Experiment 5A did not replicate the prior mechanism signal: A=0/10, B=0/10, C=0/10 mechanism matches.
3. C had 9/10 supported-oracle artifacts and 10/10 generated executable artifacts, so the negative mechanism result is not explained by wholesale planner/output invalidity.
4. C produced no eligible frozen mechanism-matched hypotheses. Experiment 5B therefore correctly stopped before direct/planner generation; it cannot support a C1-versus-C2 claim.
5. The dominant failure is mechanism transfer, followed by unrelated semantic/non-trigger behavior and some oracle/mechanical setup failures.

## Classification

**CASE 2 — mechanism transfer does not replicate.** This target does not provide evidence that structured history again improves mechanism identification. The result does not establish anything about Experiment 4 planner transfer because the required conditional sample was absent.

## Next smallest defensible experiment

Use a pre-registered second replication target with a mechanism family represented by at least two selected analogues and a target context that exposes the relevant public lifecycle/API path, then repeat 5A without prompt changes. Do not tune this run post hoc or interpret the unrun planner stage as a planner failure.

## Exact commands

```sh
python3 scripts/prepare_experiment5_target.py
PYTHONPATH=. python3 scripts/run_experiment5_end_to_end.py --attempts 10
PYTHONPATH=. python3 scripts/evaluate_experiment5.py --mode end_to_end
PYTHONPATH=. python3 scripts/select_experiment5_hypotheses.py
PYTHONPATH=. python3 scripts/run_experiment5_conditional.py
PYTHONPATH=. pytest -q tests/test_experiment4_plan_contract.py
```

The API key was loaded from `.env` into the process environment and was never printed or committed.
