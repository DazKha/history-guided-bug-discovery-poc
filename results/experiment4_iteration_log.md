# Experiment 4 append-only iteration log

Each entry is retained even when it was not selected as the preferred final refinement. No generated test or failed planner response was discarded from the artifact tree.

| Entry | Intervention | C2 planner attempts | Valid hypotheses | C2 generated / executable | C2 F2P | C2 F2P hypotheses | Decision |
|---|---|---:|---:|---:|---:|---:|---|
| E4-I1 | Strict typed plan contract, deterministic validation, two validator-directed repairs | 6 | 5/5 | 15 / 14 | 4 | 2/5 | retained as baseline contract |
| E4-I2 | Added generic assertion/lifecycle checklist to plan-to-test generation | 6 | 5/5 | 15 / 9 | 1 | 1/5 | rejected: output validity and trigger metrics regressed |
| E4-I3 | Kept contract; compact scope-safe test prompt; AST/compile/assertion preflight | 6 | 5/5 | 15 / 13 | 5 | 4/5 | retained final iteration |
| E4-I3-B | Three independent direct generations per hypothesis for equal 15-test budget | n/a | n/a | 15 / 13 | 6 | 3/5 | budget control, not an intervention refinement |

## Invalidated or diagnostic runs

- Experiment 3 natural `live1` remains an earlier diagnostic run invalidated for a hypothesis-stage parser contract bug; it is not an Experiment 4 result.
- No Experiment 4 batch was invalidated. Iteration 2 was not silently replaced: its complete CSV and artifacts remain and are explicitly reported as a negative refinement.

## Commands and controls

The three live batches used the same local `.env` API-key wrapper, model, temperature, frozen hypotheses, target context, structured history, and generation visibility. The wrapper never printed the secret. Each batch used `scripts/run_experiment4.py`; evaluation used `scripts/evaluate_experiment4.py`, which delegates buggy/fixed classification to the existing evaluator functions without modifying semantics.
