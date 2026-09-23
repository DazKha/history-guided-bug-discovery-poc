# Experiment 3 summary

## Execution status

New LLM generation did not run because `DEEPSEEK_API_KEY` was absent from the environment and empty in `.env`. The implementation therefore does not claim a completed C1/C2 comparison. Conditional C1 below is an offline replay of five previously stored mechanism-matched C tests, executed unchanged through the current evaluator.

## Observed offline conditional C1 replay

| Metric | Value |
|---|---:|
| hypotheses | 5 |
| executable tests | 5 |
| mechanism-matched rows | 5 |
| verified F2P | 2 |
| EXCEPTION_F2P | 2 |
| F2F | 1 |
| P2P | 2 |
| activated buggy executions | 3 |

This replay reproduces stored Experiment 2 evidence and is not evidence that the new planner improves trigger construction. C2 has no generated candidates, so diversity yield, trigger-to-F2P improvement, and budget-normalized causal comparison are undefined.

## Required comparison status

| Mode | C1 | C2 | Comparison |
|---|---|---|---|
| 3A natural | blocked | blocked | not estimable |
| 3B conditional | stored-test replay | blocked | not estimable |

## Interpretation

The available evidence supports only that the existing evaluator still recognizes the two previously observed exception-based F2P cases when their unchanged tests are replayed. It does not support any claim about trigger diversification. The single next action is to provide the required API credential, rerun the exact commands in the reviewer report, and then compare C1/C2 with the predeclared budget metrics.