# Final failure analysis

The corrected criterion is: `verified_f2p = same unchanged test on buggy and fixed AND buggy has a meaningful semantic failure AND fixed passes AND oracle was supported before execution`. Meaningful semantic failure is either an assertion failure or a target exception that violates that pre-execution oracle. Setup/environment exceptions remain mechanical.

## Aggregate Experiment 2 evidence

| Condition | Attempts | Mechanism Matches | Supported Hypotheses | Executable Tests | Assertion F2P | Exception F2P | Total Verified F2P | P2P | F2F | Mechanical | Unsupported Oracles | No-Supported/Model | False/Unverified | LLM Calls | Tokens (prompt/completion) | Wall Clock (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 25 | 0 | 23 | 24 | 0 | 0 | 0 | 21 | 2 | 0 | 1 | 1 | 25 | 25 | 367421/15442 | 85.774 |
| B | 25 | 2 | 22 | 22 | 0 | 0 | 0 | 21 | 1 | 0 | 0 | 3 | 25 | 25 | 433454/13953 | 103.216 |
| C | 25 | 15 | 23 | 23 | 0 | 2 | 2 | 16 | 5 | 0 | 0 | 2 | 23 | 25 | 371836/21038 | 120.701 |

The aggregate includes 25 attempts per condition: 15 preserved prior attempts and 10 new replication attempts. The only verified F2P results are two `EXCEPTION_F2P` cases in exploratory C. There are no assertion F2P results.

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

## Batch: replication2 (10 new attempts/condition)

| Condition | Attempts | Mechanism Matches | Supported Hypotheses | Executable Tests | Assertion F2P | Exception F2P | Total Verified F2P | P2P | F2F | Mechanical | Unsupported Oracles | No-Supported/Model | False/Unverified | LLM Calls | Tokens (prompt/completion) | Wall Clock (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 10 | 0 | 9 | 10 | 0 | 0 | 0 | 8 | 1 | 0 | 1 | 0 | 10 | 10 | 153190/5698 | 33.552 |
| B | 10 | 1 | 10 | 10 | 0 | 0 | 0 | 10 | 0 | 0 | 0 | 0 | 10 | 10 | 197110/6469 | 39.437 |
| C | 10 | 6 | 10 | 10 | 0 | 0 | 0 | 8 | 2 | 0 | 0 | 0 | 10 | 10 | 161770/9015 | 48.493 |

## Replication C mechanism matches without F2P

- `replication2b_C_02`: `P2P` / `TRIGGER_TOO_WEAK`; buggy/fixed `PASS` / `PASS`.
- `replication2b_C_03`: `P2P` / `TRIGGER_TOO_WEAK`; buggy/fixed `PASS` / `PASS`.
- `replication2c_C_02`: `P2P` / `TRIGGER_TOO_WEAK`; buggy/fixed `PASS` / `PASS`.
- `replication2c_C_03`: `F2F` / `TRIGGER_WRONG_SHAPE`; buggy/fixed `ASSERTION_FAILURE` / `ASSERTION_FAILURE`.
- `replication2c_C_04`: `F2F` / `TRIGGER_WRONG_SHAPE`; buggy/fixed `ASSERTION_FAILURE` / `ASSERTION_FAILURE`.
- `replication2c_C_05`: `P2P` / `TRIGGER_TOO_WEAK`; buggy/fixed `PASS` / `PASS`.

## Localized failure analysis

- A generated plausible target behavior but did not match the locale-dependent encoding mechanism in any batch; its executable tests were P2P or model errors.
- B occasionally picked up adjacent file-output or encoding language, but did not produce a verified F2P; raw history remained distracted by unrelated state/path hypotheses.
- C identified the true encoding mechanism repeatedly (15/25 aggregate mechanism-match labels). Two exploratory C tests directly exercised the public path-output API and produced target `UnicodeEncodeError` on buggy with fixed passes; these are valid exception-based F2P under the corrected rule.
- Later strict and replication C attempts did not reproduce F2P: the strict batch had two model errors, two P2P tests, and one F2F; the 10-attempt replication had six mechanism matches, two F2F, and eight P2P with no F2P. This localizes the remaining instability to trigger/test construction, not historical mechanism identification.
- Within the 10-attempt replication, the six C mechanism matches that were not F2P were four `TRIGGER_TOO_WEAK` P2P cases and two `TRIGGER_WRONG_SHAPE` F2F cases (the latter also had assertions misaligned with the observable behavior).
- No tests were edited between buggy and fixed execution. The exploratory oracle and hypothesis are taken from the stored model artifact created before execution; the evaluator does not rewrite them after observing outcomes.

## Conclusion

In this retrospectively selected transfer-feasibility case, structured historical knowledge identified the correct failure mechanism and produced verified executable evidence distinguishing the buggy and fixed revisions. The evidence does not prove the architecture: the two valid F2P cases occur in one exploratory batch, later attempts did not reproduce them, and A/B did not produce valid F2P. The stable conclusion is that structured history improves search direction here, while robust trigger construction remains the bottleneck.
