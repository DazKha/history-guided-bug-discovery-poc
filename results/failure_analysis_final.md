# Final failure analysis

The corrected criterion is: `verified_f2p = same unchanged test on buggy and fixed AND buggy has a meaningful semantic failure AND fixed passes AND oracle was supported before execution`. Meaningful semantic failure is either an assertion failure or a target exception that violates that pre-execution oracle. Setup/environment exceptions remain mechanical.

## Aggregate Experiment 2 evidence

| Condition | Attempts | Mechanism Matches | Supported Hypotheses | Executable Tests | Assertion F2P | Exception F2P | Total Verified F2P | P2P | F2F | Mechanical | Unsupported Oracles | No-Supported/Model | False/Unverified | LLM Calls | Tokens (prompt/completion) | Wall Clock (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 15 | 0 | 14 | 14 | 0 | 0 | 0 | 13 | 1 | 0 | 0 | 1 | 15 | 15 | 214231/9744 | 52.222 |
| B | 15 | 1 | 12 | 12 | 0 | 0 | 0 | 11 | 1 | 0 | 0 | 3 | 15 | 15 | 236344/7484 | 63.779 |
| C | 15 | 9 | 13 | 13 | 0 | 2 | 2 | 8 | 3 | 0 | 0 | 2 | 13 | 15 | 210066/12023 | 72.208 |

The aggregate includes 15 attempts per condition: the preserved exploratory batch, the later strict batch, and one additional uniform looped batch. The only verified F2P results are two `EXCEPTION_F2P` cases in exploratory C. There are no assertion F2P results.

## Batch: exploratory

| Condition | Attempts | Mechanism Matches | Supported Hypotheses | Executable Tests | Assertion F2P | Exception F2P | Total Verified F2P | P2P | F2F | Mechanical | Unsupported Oracles | No-Supported/Model | False/Unverified | LLM Calls | Tokens (prompt/completion) | Wall Clock (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 5 | 0 | 5 | 5 | 0 | 0 | 0 | 4 | 1 | 0 | 0 | 0 | 5 | 5 | 76360/3895 | 20.196 |
| B | 5 | 0 | 4 | 4 | 0 | 0 | 0 | 3 | 1 | 0 | 0 | 1 | 5 | 5 | 78656/2484 | 22.885 |
| C | 5 | 4 | 5 | 5 | 0 | 2 | 2 | 2 | 1 | 0 | 0 | 0 | 3 | 5 | 80650/4646 | 22.006 |

## Batch: final

| Condition | Attempts | Mechanism Matches | Supported Hypotheses | Executable Tests | Assertion F2P | Exception F2P | Total Verified F2P | P2P | F2F | Mechanical | Unsupported Oracles | No-Supported/Model | False/Unverified | LLM Calls | Tokens (prompt/completion) | Wall Clock (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 5 | 0 | 5 | 5 | 0 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 5 | 5 | 76595/3007 | 15.35 |
| B | 5 | 0 | 4 | 4 | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 1 | 5 | 5 | 78844/2419 | 22.512 |
| C | 5 | 2 | 3 | 3 | 0 | 0 | 0 | 2 | 1 | 0 | 0 | 2 | 5 | 5 | 48531/2813 | 26.94 |

## Batch: loop1

| Condition | Attempts | Mechanism Matches | Supported Hypotheses | Executable Tests | Assertion F2P | Exception F2P | Total Verified F2P | P2P | F2F | Mechanical | Unsupported Oracles | No-Supported/Model | False/Unverified | LLM Calls | Tokens (prompt/completion) | Wall Clock (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 5 | 0 | 4 | 4 | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 1 | 5 | 5 | 61276/2842 | 16.676 |
| B | 5 | 1 | 4 | 4 | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 1 | 5 | 5 | 78844/2581 | 18.382 |
| C | 5 | 3 | 5 | 5 | 0 | 0 | 0 | 4 | 1 | 0 | 0 | 0 | 5 | 5 | 80885/4564 | 23.262 |

## Localized failure analysis

- A generated plausible target behavior but did not match the locale-dependent encoding mechanism in any batch; its executable tests were P2P or model errors.
- B occasionally picked up adjacent file-output or encoding language, but did not produce a verified F2P; raw history remained distracted by unrelated state/path hypotheses.
- C identified the true encoding mechanism repeatedly (9/15 aggregate mechanism-match labels). Two exploratory C tests directly exercised the public path-output API and produced target `UnicodeEncodeError` on buggy with fixed passes; these are valid exception-based F2P under the corrected rule.
- Later strict and looped C attempts did not reproduce F2P: the strict batch had two model errors, two P2P tests, and one F2F; the looped batch had four P2P tests and one F2F despite three mechanism matches. This localizes the remaining instability to trigger/test construction, not historical mechanism identification.
- No tests were edited between buggy and fixed execution. The exploratory oracle and hypothesis are taken from the stored model artifact created before execution; the evaluator does not rewrite them after observing outcomes.

## Conclusion

In this retrospectively selected transfer-feasibility case, structured historical knowledge identified the correct failure mechanism and produced verified executable evidence distinguishing the buggy and fixed revisions. The evidence does not prove the architecture: the two valid F2P cases occur in one exploratory batch, later attempts did not reproduce them, and A/B did not produce valid F2P. The stable conclusion is that structured history improves search direction here, while robust trigger construction remains the bottleneck.
