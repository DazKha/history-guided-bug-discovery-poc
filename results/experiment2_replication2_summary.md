# Experiment 2 re-evaluated summary

Verified F2P requires the same unchanged test on buggy and fixed, a meaningful semantic buggy failure, a fixed pass, and an oracle supported before execution. Meaningful failure includes an assertion failure or a target exception that violates that pre-execution oracle. Target exceptions that are setup/environment failures or unrelated to the hypothesis remain mechanical.

## replication2

| Condition | Attempts | Mechanism matches | Supported hypotheses | Executable tests | Assertion F2P | Exception F2P | Total verified F2P | P2P | F2F | Mechanical | Unsupported oracle | No-supported/model error | False/unverified | LLM calls | Prompt tokens | Completion tokens | Wall clock |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 10 | 0 | 9 | 10 | 0 | 0 | 0 | 8 | 1 | 0 | 1 | 0 | 10 | 10 | 153190 | 5698 | 33.552 |
| B | 10 | 1 | 10 | 10 | 0 | 0 | 0 | 10 | 0 | 0 | 0 | 0 | 10 | 10 | 197110 | 6469 | 39.437 |
| C | 10 | 6 | 10 | 10 | 0 | 0 | 0 | 8 | 2 | 0 | 0 | 0 | 10 | 10 | 161770 | 9015 | 48.493 |

The final strict run is reported separately from the exploratory run. No tests were edited between buggy/fixed execution.
