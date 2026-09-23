# Experiment 2 re-evaluated summary

Verified F2P requires the same unchanged test on buggy and fixed, a meaningful semantic buggy failure, a fixed pass, and an oracle supported before execution. Meaningful failure includes an assertion failure or a target exception that violates that pre-execution oracle. Target exceptions that are setup/environment failures or unrelated to the hypothesis remain mechanical.

## exploratory

| Condition | Attempts | Mechanism matches | Supported hypotheses | Executable tests | Assertion F2P | Exception F2P | Total verified F2P | P2P | F2F | Mechanical | Unsupported oracle | No-supported/model error | False/unverified | LLM calls | Prompt tokens | Completion tokens | Wall clock |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 5 | 0 | 5 | 5 | 0 | 0 | 0 | 4 | 1 | 0 | 0 | 0 | 5 | 5 | 76360 | 3895 | 20.196 |
| B | 5 | 0 | 4 | 4 | 0 | 0 | 0 | 3 | 1 | 0 | 0 | 1 | 5 | 5 | 78656 | 2484 | 22.885 |
| C | 5 | 4 | 5 | 5 | 0 | 2 | 2 | 2 | 1 | 0 | 0 | 0 | 3 | 5 | 80650 | 4646 | 22.006 |

## final

| Condition | Attempts | Mechanism matches | Supported hypotheses | Executable tests | Assertion F2P | Exception F2P | Total verified F2P | P2P | F2F | Mechanical | Unsupported oracle | No-supported/model error | False/unverified | LLM calls | Prompt tokens | Completion tokens | Wall clock |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 5 | 0 | 5 | 5 | 0 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 5 | 5 | 76595 | 3007 | 15.35 |
| B | 5 | 0 | 4 | 4 | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 1 | 5 | 5 | 78844 | 2419 | 22.512 |
| C | 5 | 2 | 3 | 3 | 0 | 0 | 0 | 2 | 1 | 0 | 0 | 2 | 5 | 5 | 48531 | 2813 | 26.94 |

## loop1

| Condition | Attempts | Mechanism matches | Supported hypotheses | Executable tests | Assertion F2P | Exception F2P | Total verified F2P | P2P | F2F | Mechanical | Unsupported oracle | No-supported/model error | False/unverified | LLM calls | Prompt tokens | Completion tokens | Wall clock |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 5 | 0 | 4 | 4 | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 1 | 5 | 5 | 61276 | 2842 | 16.676 |
| B | 5 | 1 | 4 | 4 | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 1 | 5 | 5 | 78844 | 2581 | 18.382 |
| C | 5 | 3 | 5 | 5 | 0 | 0 | 0 | 4 | 1 | 0 | 0 | 0 | 5 | 5 | 80885 | 4564 | 23.262 |

## replication2b

| Condition | Attempts | Mechanism matches | Supported hypotheses | Executable tests | Assertion F2P | Exception F2P | Total verified F2P | P2P | F2F | Mechanical | Unsupported oracle | No-supported/model error | False/unverified | LLM calls | Prompt tokens | Completion tokens | Wall clock |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 5 | 0 | 4 | 5 | 0 | 0 | 0 | 3 | 1 | 0 | 1 | 0 | 5 | 5 | 76595 | 2814 | 16.182 |
| B | 5 | 0 | 5 | 5 | 0 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 5 | 5 | 98555 | 3516 | 20.981 |
| C | 5 | 2 | 5 | 5 | 0 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 5 | 5 | 80885 | 4059 | 22.538 |

## replication2c

| Condition | Attempts | Mechanism matches | Supported hypotheses | Executable tests | Assertion F2P | Exception F2P | Total verified F2P | P2P | F2F | Mechanical | Unsupported oracle | No-supported/model error | False/unverified | LLM calls | Prompt tokens | Completion tokens | Wall clock |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 5 | 0 | 5 | 5 | 0 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 5 | 5 | 76595 | 2884 | 17.37 |
| B | 5 | 1 | 5 | 5 | 0 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 5 | 5 | 98555 | 2953 | 18.456 |
| C | 5 | 4 | 5 | 5 | 0 | 0 | 0 | 3 | 2 | 0 | 0 | 0 | 5 | 5 | 80885 | 4956 | 25.955 |

## Decision on the Unicode case

Exploratory C attempt 1 is classified as `EXCEPTION_F2P`: the pre-execution artifact contains an encoding-specific hypothesis and target-supported oracle, the buggy traceback is `UnicodeEncodeError` at `pysnooper/tracer.py:134`, and the unchanged test passes on fixed. This is not retroactive oracle invention.

The final strict run is reported separately from the exploratory run. No tests were edited between buggy/fixed execution.
