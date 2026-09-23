# Experiment 5 budget analysis

All three end-to-end conditions used 10 independent model calls. No repair loop or planner was used in 5A, and no 5B calls were made because the eligible frozen-hypothesis count was zero.

| Condition | LLM calls | Prompt tokens | Completion tokens | Wall-clock seconds | Generated tests | Executable tests | F2P | F2P/call | F2P/executable test |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A target only | 10 | 114,770 | 5,621 | 37.504 | 10 | 10 | 0 | 0.0% | 0.0% |
| B raw history | 10 | 142,497 | 4,598 | 42.723 | 7 | 7 | 0 | 0.0% | 0.0% |
| C structured history | 10 | 122,830 | 9,735 | 52.826 | 10 | 10 | 0 | 0.0% | 0.0% |
| Total | 30 | 380,097 | 19,954 | 133.053 | 27 | 27 | 0 | 0.0% | 0.0% |

Executions per verified F2P, LLM calls per verified F2P, tokens per verified F2P, and time to first F2P are undefined because no verified F2P occurred. A budget-matched C1/C2 comparison is also undefined because no eligible frozen C hypothesis existed.

The relevant comparison is therefore not planner efficiency but transfer validity: C had the same 10-attempt budget as A/B, produced 10 executable tests, and still produced 0/10 target-mechanism matches.
