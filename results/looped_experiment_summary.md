# Experiment 2 re-evaluated summary

Verified F2P requires the same unchanged test on buggy and fixed, a meaningful semantic buggy failure, a fixed pass, and an oracle supported before execution. Meaningful failure includes an assertion failure or a target exception that violates that pre-execution oracle. Target exceptions that are setup/environment failures or unrelated to the hypothesis remain mechanical.

## loop1

| Condition | Attempts | Mechanism matches | Supported hypotheses | Executable tests | Assertion F2P | Exception F2P | Total verified F2P | P2P | F2F | Mechanical | Unsupported oracle | No-supported/model error | False/unverified | LLM calls | Prompt tokens | Completion tokens | Wall clock |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 5 | 0 | 4 | 4 | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 1 | 5 | 5 | 61276 | 2842 | 16.676 |
| B | 5 | 1 | 4 | 4 | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 1 | 5 | 5 | 78844 | 2581 | 18.382 |
| C | 5 | 3 | 5 | 5 | 0 | 0 | 0 | 4 | 1 | 0 | 0 | 0 | 5 | 5 | 80885 | 4564 | 23.262 |

The final strict run is reported separately from the exploratory run. No tests were edited between buggy/fixed execution.
