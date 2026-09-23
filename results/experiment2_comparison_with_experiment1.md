# Experiment 2 comparison with Experiment 1

| Experiment | Condition | Attempts | Tests | F2P | P2P | F2F | Mechanical | Abstentions/model errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Exp1 | A target-only | 5 | 4 | 0 | 3 | 0 | 1 | 1 no-support |
| Exp1 | B raw history | 5 | 0 | 0 | 0 | 0 | 0 | 5 no-support |
| Exp1 | C structured | 5 | 0 | 0 | 0 | 0 | 0 | 5 no-support |
| Exp2 final | A target-only | 5 | 5 | 0 | 5 | 0 | 0 | 0 |
| Exp2 final | B raw history | 5 | 4 | 0 | 4 | 0 | 0 | 1 model error |
| Exp2 final | C structured | 5 | 3 | 0 | 2 | 1 | 0 | 2 model errors |

Exp1 was inconclusive because the raw baseline did not receive the raw fix diff containing the strongest transferable evidence, the common prompt applied C-style abstention to B, the structured fields were generic, and target runtime locale facts were omitted from the context.

Exp2 controlled those confounds: it used the same small historical subset for B/C, included the actual raw diffs for B, used concise mechanism-centered units for C, exposed only ordinary target source/docs/tests plus runtime facts, and applied the applicability gate only to C. The final strict run still produced no assertion-level F2P result. C generated the most mechanism-aligned hypotheses, but one was P2P and one F2F; A and B generated no mechanism-aligned hypothesis in this sample.

The preserved exploratory run contains an exception-level buggy/fixed split for a C encoding test. It is disclosed but not promoted to F2P because it did not meet the predeclared assertion-level criterion. The follow-up conclusion is therefore: Exp2 demonstrates improved mechanism targeting and a real near-transfer signal, but not verified positive discovery superiority.

## Evaluator-corrected interpretation

The exception-level rule was subsequently audited and corrected. A target-origin exception can be meaningful when it violates a pre-execution supported oracle, occurs in target behavior, and the exact unchanged test passes on fixed. Re-evaluation of all preserved artifacts found two valid `EXCEPTION_F2P` cases in exploratory C. A further uniform five-attempt batch per condition produced no additional F2P.

Across 15 attempts per condition after combining the preserved exploratory, strict, and looped batches: A had 0 F2P/0 mechanism matches; B had 0 F2P/1 mechanism match; C had 2 exception F2P/9 mechanism matches. The corrected conclusion is limited positive transfer feasibility for the retrospectively selected case, with unstable trigger construction and no evidence of general architecture superiority.
