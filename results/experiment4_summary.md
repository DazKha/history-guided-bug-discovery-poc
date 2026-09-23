# Experiment 4 summary

## Outcome

The intervention improved plan validity and increased hypothesis-level F2P coverage, but it did not improve budget-normalized trigger efficiency. The defensible classification is **CASE B / mixed result**: the plan contract solved a real planner-validity problem and the final compact generation refinement produced C2 F2P for 4/5 frozen hypotheses, but C2 remained less efficient per generated/executable test than the budget-matched direct control.

The result is based on five frozen hypotheses, so it is directional evidence, not a significance claim. It is evidence from one selected target and makes no cross-project generalization claim.

## What changed

Experiment 4 added a separate path in `scripts/run_experiment4.py` and `scripts/evaluate_experiment4.py`:

`frozen hypothesis -> strict Trigger Plan -> deterministic validation -> up to two validator-directed repairs -> test generation -> unchanged evaluator`

The plan contract requires preconditions, initial state, ordered typed actions, expected invariant, observable source/measurement/extraction, assertion predicate/failure condition/rationale, setup, and timeout. Validation is generic and uses only the frozen hypothesis and the visible buggy target context. Generated test code receives a final syntax/assertion preflight before target execution.

Three refinement iterations were run:

1. Strict plan schema and deterministic validator.
2. Added explicit generic assertion/lifecycle guidance. This regressed test-generation validity and was not retained as the preferred refinement.
3. Kept the strict validator, made test generation compact and scope-safe, and added AST/compile/assertion preflight. This was the retained final iteration.

## Frozen controls

The following remained unchanged: target and repositories, structured historical memory, the five stored hypotheses, target context, model (`deepseek-flash`), temperature, oracle policy, execution environment, leakage controls, fixed-revision evaluator-only access, evaluator semantics, and all Experiment 2 code/results.

The evaluator still requires the same unchanged test to fail semantically on buggy, pass on fixed, and use a supported pre-execution oracle. No target-specific rule was added to the planner or validator.

## Final iteration results

| Arm | Hypotheses | Allocated candidate slots | Generated test artifacts | Executed test artifacts | F2P | Hypotheses with F2P | F2P/slot | F2P/generated artifact |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| C1 direct | 5 | 5 | 5 | 5 | 2 | 2/5 (40%) | 40.0% | 40.0% |
| C2 strict planner | 5 | 15 | 13 | 13 | 5 | 4/5 (80%) | 33.3% | 38.5% |
| C1 budget-matched direct | 5 | 15 | 13 | 13 | 6 | 3/5 (60%) | 40.0% | 46.2% |

C2's five F2P tests came from four hypotheses. The 15-slot C1 budget control produced 13 generated/executed test artifacts with the same direct-test prompt, three independent direct calls per frozen hypothesis, and the same evaluator.

## Planner and failure metrics

- Final C2 valid plans: 5/5 hypotheses.
- Planner attempts: 6; five valid first responses and one malformed first response repaired successfully.
- Planner validation rejection rate: 1/6 (16.7%).
- Repair success rate: 1/1 rejected planner attempts repaired to a valid plan set.
- Final C2: 15 allocated candidate slots, 13 generated test artifacts, and 13 executed test artifacts.
- Final C2 test outcomes: 5 F2P, 0 F2F, 3 P2P, 5 mechanical failures, 2 model-output failures.
- Final C1 budget-matched outcomes: 6 F2P, 2 F2F, 5 P2P, 2 model-output failures.

## Interpretation

Compared with the budget-matched direct control, C2 improved hypothesis-level coverage from 3/5 to 4/5. It produced 5/15 F2P tests versus 6/15 for C1 budget-matched, so it did not improve F2P per generated candidate. C2 required 21 LLM calls and 326,930 recorded tokens versus 15 calls and 15,801 tokens for C1. Compared with Experiment 3 C2 (2/5 hypotheses with F2P and 2/5 valid planner outputs), Experiment 4 C2 reached 4/5 hypotheses with F2P and 5/5 valid final planner outputs. The evidence supports improved conversion coverage through bounded structured search, not a claim that each candidate became more effective.

The dominant remaining failure mode in the retained run was generated-test instantiation: five mechanical failures and three P2P results. The next smallest defensible change is generic pre-execution collection/runtime validation with one bounded repair, not another increase in planner breadth or a change to historical memory.

## Commands

```text
python3 -m pytest -q
python3 scripts/verify_harness.py
python3 -m py_compile scripts/experiment4_plan_contract.py scripts/run_experiment4.py scripts/evaluate_experiment4.py
python3 -m pytest -q tests/test_experiment4_plan_contract.py
python3 scripts/evaluate_experiment4.py --iteration 1
python3 scripts/evaluate_experiment4.py --iteration 2
python3 scripts/evaluate_experiment4.py --iteration 3 --arms C1,C2
python3 scripts/evaluate_experiment4.py --iteration 3 --arms C1_BUDGETED --output-suffix _budgeted
```

The live-generation command used a short Python wrapper to read `DEEPSEEK_API_KEY` from the local `.env` without printing or logging it, then invoked `scripts.run_experiment4` for `--iteration 1`, `--iteration 2`, `--iteration 3`, and `--arm C1B`.

## Artifacts

- [experiment4_results.csv](experiment4_results.csv)
- [experiment4_failure_analysis.md](experiment4_failure_analysis.md)
- [experiment4_budget_analysis.md](experiment4_budget_analysis.md)
- [experiment4_iteration_log.md](experiment4_iteration_log.md)
- [experiment4_reviewer_report.md](experiment4_reviewer_report.md)
- [experiment4_run_status.json](experiment4_run_status.json)
- `artifacts/experiment4/iteration{1,2,3}/`
- `artifacts/execution_logs/experiment4/iteration{1,2,3}/`
- `generated_tests/experiment4/iteration{1,2,3}/`
