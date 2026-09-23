# Experiment 4 failure analysis

## Taxonomy

The validator and evaluator keep infrastructure, planning, generation, and semantic outcomes separate. A plan rejection is not counted as a target execution. A mechanical failure is not a semantic failure and cannot become F2P.

### Planner failures

All three iterations had the same one rejected initial planner response:

| Iteration | Hypothesis | Attempt | Category | Result |
|---|---|---:|---|---|
| 1 | conditional-h03-768b90f0a5 | 0 | MALFORMED_SCHEMA | unterminated JSON string; repaired on attempt 1 |
| 2 | conditional-h03-768b90f0a5 | 0 | MALFORMED_SCHEMA | unterminated JSON string; repaired on attempt 1 |
| 3 | conditional-h03-768b90f0a5 | 0 | MALFORMED_SCHEMA | unterminated JSON string; repaired on attempt 1 |

No unsupported action, missing required field, unsupported observable, leakage, or inconsistent action-order rejection occurred in the final plan batches. The strict validator reached a valid plan set for every frozen hypothesis.

### Final iteration C2

| Hypothesis | Plan | Outcome | Diagnosis |
|---|---|---|---|
| h01 | 1, 2, 3 | MODEL_ERROR, 2 F2P | One candidate was rejected as model output; two valid realizations worked. |
| h02 | 1, 2, 3 | 3 MECHANICAL_FAILURE | All three generated tests failed in setup/fixture/runtime plumbing before a semantic comparison. |
| h03 | 1, 2, 3 | P2P, F2P, P2P | One source-decoding realization worked; two did not activate the intended semantic difference. |
| h04 | 1, 2, 3 | F2P, MECHANICAL_FAILURE, MODEL_ERROR | One realization worked; the other two failed in mechanics or model output. |
| h05 | 1, 2, 3 | MECHANICAL_FAILURE, F2P, P2P | One realization worked; the other two failed mechanically or did not activate the mechanism. |

### Every F2F result across the refinement ledger

| Iteration | Arm | Hypothesis / trigger | Buggy failure | Fixed failure | Classification |
|---|---|---|---|---|---|
| 1 | C2 | h02 / plan-1 | UnicodeEncodeError | UnicodeEncodeError | same target exception on both revisions |
| 1 | C2 | h02 / plan-3 | AssertionError | AssertionError | same assertion failed on both revisions |
| 2 | C1 | h02 / direct | UnicodeEncodeError | UnicodeEncodeError | direct baseline also fails on both |
| 2 | C2 | h01 / plan-3 | AssertionError | AssertionError | assertion/observable did not distinguish revisions |
| 2 | C2 | h02 / plan-1 | AssertionError | AssertionError | assertion/observable did not distinguish revisions |
| 2 | C2 | h04 / plan-1 | AssertionError | AssertionError | assertion/observable did not distinguish revisions |
| 3 | C1 | h02 / direct | UnicodeEncodeError | UnicodeEncodeError | direct baseline also fails on both |

The final C2 run had no F2F, but this ledger shows that the generic plan contract alone did not eliminate assertion/lifecycle non-discrimination in iteration 1 or 2. No F2F row was removed from accounting.

### Other final-iteration failures

- `P2P` (3 C2, 5 budgeted direct): intended target behavior was not activated; this is `TRIGGER_TOO_WEAK`, not a verifier failure.
- `MECHANICAL_FAILURE` (5 C2): generated tests failed in setup/collection/runtime plumbing, including undefined child-module names or output/encoding handling before a supported semantic oracle was reached.
- `MODEL_ERROR` (2 C2, 2 budgeted direct): test response was empty, malformed, or rejected by the existing safety parser. These calls remain in the budget.
- No evaluator or harness defect was found. The harness regression check continues to report `{"buggy": 1, "fixed": 0}` and the repository suite passes.

## Root-cause summary

1. Planner validity was a real infrastructure bottleneck and was improved by strict schema plus bounded repair.
2. Plan validity did not guarantee executable code: generated test scope, subprocess output encoding, and fixture/setup consistency remained failure points.
3. A correct trigger can still produce F2F when the observation/assertion does not discriminate revisions, especially for h02's artificial stderr stream.
4. The final compact prompt reduced model-output failures relative to iteration 2 but did not improve per-test efficiency over direct generation.
