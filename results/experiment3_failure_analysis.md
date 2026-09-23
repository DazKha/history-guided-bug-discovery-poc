# Experiment 3 failure analysis

No new C2 trigger candidates were generated because the model credential was unavailable. Therefore no new trigger-level failure taxonomy can be inferred. The five offline C1 replay rows are retained without filtering:

| Hypothesis | Classification | Activation | Failure category |
|---|---|---|---|
| conditional-h01 | EXCEPTION_F2P | ACTIVATED | VALID_EXCEPTION_F2P |
| conditional-h02 | F2F | ACTIVATED | SEMANTIC_NON_TRIGGER |
| conditional-h03 | P2P | NOT_ACTIVATED | TRIGGER_TOO_WEAK |
| conditional-h04 | EXCEPTION_F2P | ACTIVATED | VALID_EXCEPTION_F2P |
| conditional-h05 | P2P | NOT_ACTIVATED | TRIGGER_TOO_WEAK |

The replay contains two valid exception-based F2P rows, one F2F row, and two P2P rows. These are unchanged prior tests and must not be attributed to the new intervention.

No rows were discarded because of outcome. No thresholds or oracle rules were changed.
