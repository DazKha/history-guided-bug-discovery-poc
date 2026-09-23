# Experiment 2 cumulative summary

Previous results are the preserved exploratory, strict, and loop1 batches (15 attempts per condition); the new replication is the combined `replication2b` + `replication2c` batches (10 new attempts per condition). The two five-attempt halves preserve the existing frozen prompt, which states the attempt index within a five-attempt batch. The table below combines every evaluated batch without deleting prior artifacts.

## Previous batches

| Condition | Attempts | Mechanism Matches | Supported Hypotheses | Executable Tests | Assertion F2P | Exception F2P | Total Verified F2P | P2P | F2F | Mechanical | Unsupported Oracles | No-Supported/Model | False/Unverified | LLM Calls | Tokens (prompt/completion) | Wall Clock (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 15 | 0 | 14 | 14 | 0 | 0 | 0 | 13 | 1 | 0 | 0 | 1 | 15 | 15 | 214231/9744 | 52.222 |
| B | 15 | 1 | 12 | 12 | 0 | 0 | 0 | 11 | 1 | 0 | 0 | 3 | 15 | 15 | 236344/7484 | 63.779 |
| C | 15 | 9 | 13 | 13 | 0 | 2 | 2 | 8 | 3 | 0 | 0 | 2 | 13 | 15 | 210066/12023 | 72.208 |

## New replication batch

| Condition | Attempts | Mechanism Matches | Supported Hypotheses | Executable Tests | Assertion F2P | Exception F2P | Total Verified F2P | P2P | F2F | Mechanical | Unsupported Oracles | No-Supported/Model | False/Unverified | LLM Calls | Tokens (prompt/completion) | Wall Clock (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 10 | 0 | 9 | 10 | 0 | 0 | 0 | 8 | 1 | 0 | 1 | 0 | 10 | 10 | 153190/5698 | 33.552 |
| B | 10 | 1 | 10 | 10 | 0 | 0 | 0 | 10 | 0 | 0 | 0 | 0 | 10 | 10 | 197110/6469 | 39.437 |
| C | 10 | 6 | 10 | 10 | 0 | 0 | 0 | 8 | 2 | 0 | 0 | 0 | 10 | 10 | 161770/9015 | 48.493 |

## Cumulative

| Condition | Attempts | Mechanism Matches | Supported Hypotheses | Executable Tests | Assertion F2P | Exception F2P | Total Verified F2P | P2P | F2F | Mechanical | Unsupported Oracles | No-Supported/Model | False/Unverified | LLM Calls | Tokens (prompt/completion) | Wall Clock (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 25 | 0 | 23 | 24 | 0 | 0 | 0 | 21 | 2 | 0 | 1 | 1 | 25 | 25 | 367421/15442 | 85.774 |
| B | 25 | 2 | 22 | 22 | 0 | 0 | 0 | 21 | 1 | 0 | 0 | 3 | 25 | 25 | 433454/13953 | 103.216 |
| C | 25 | 15 | 23 | 23 | 0 | 2 | 2 | 16 | 5 | 0 | 0 | 2 | 23 | 25 | 371836/21038 | 120.701 |

The cumulative evidence contains two verified exception-based F2P cases, both in preserved exploratory C. The new replication produced no F2P, so the prior observation did not reproduce in the new batch even though C retained more mechanism matches than A/B.
