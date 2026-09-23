# Experiment 3 budget analysis

## Planned budget

C1 uses one direct test per frozen hypothesis. C2 uses one planner call plus up to four test-generation calls per frozen hypothesis. Every retained test is executed once on buggy and once on fixed. C2 therefore costs more execution and LLM budget by design; F2P counts must be normalized by hypotheses, executed tests, calls, tokens, and time.

## Observed budget

| Mode/arm | Hypotheses | Generated tests | Buggy/fixed pairs | LLM calls | Status |
|---|---:|---:|---:|---:|---|
| conditional/C1 replay | 5 | 5 | 10 | 0 new | completed replay |
| natural/C1 | 0 | 0 | 0 | 0 | blocked |
| natural/C2 | 0 | 0 | 0 | 0 | blocked |
| conditional/C2 | 0 | 0 | 0 | 0 | blocked |

Because C2 did not run, executions per verified F2P for the new intervention, calls/tokens per verified F2P, time to first new F2P, and budget-normalized C1/C2 differences are undefined. The replay's two F2P cases are historical baseline evidence only.