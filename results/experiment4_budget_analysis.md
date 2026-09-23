# Experiment 4 budget analysis

## Budget-matched comparison

The primary final comparison uses 15 generated-test opportunities per arm. C2 obtains 15 opportunities as three validated plans per hypothesis. C1_BUDGETED obtains 15 opportunities as three independent direct generations per hypothesis. Both arms use the same five frozen hypotheses and evaluator.

| Metric | C2 strict planner | C1_BUDGETED direct | Interpretation |
|---|---:|---:|---|
| Generated tests | 15 | 15 | matched |
| Executable tests | 13 | 13 | matched |
| F2P tests | 5 | 6 | direct control higher |
| Hypotheses with F2P | 4/5 (80%) | 3/5 (60%) | planner higher coverage |
| F2P / generated test | 33.3% | 40.0% | direct higher |
| F2P / executable test | 38.5% | 46.2% | direct higher |
| Executions / F2P | 2.60 | 2.17 | direct more efficient |
| LLM calls | 21 | 15 | planner includes 6 planner attempts |
| LLM calls / F2P | 4.20 | 2.50 | direct cheaper |
| Tokens, prompt + completion | 326,930 | 15,801 | planner substantially more expensive |
| Tokens / F2P | 65,386 | 2,634 | planner substantially more expensive |

The planner's 21 calls are 15 test-generation calls plus 6 plan calls (five initial responses and one repair). The budgeted direct arm has 15 direct test-generation calls.

## Iteration trend

| Iteration | C2 valid hypotheses | C2 executable / generated | C2 F2P | C2 F2P hypotheses | C2 F2P / generated |
|---|---:|---:|---:|---:|---:|
| 1 | 5/5 | 14/15 | 4 | 2/5 | 26.7% |
| 2 | 5/5 | 9/15 | 1 | 1/5 | 6.7% |
| 3 | 5/5 | 13/15 | 5 | 4/5 | 33.3% |

Iteration 2 shows why hypothesis-level results alone are unsafe: its validator remained successful while test-generation failures increased. Iteration 3 restored executable output with a compact, scope-safe prompt, but the final normalized rate still did not exceed the direct budget control.

## Time and cost signals

In the sequential evaluator logs, the first final-iteration F2P appeared after approximately 3.35 seconds for C1, 6.52 seconds for C2, and 2.72 seconds for C1_BUDGETED. These are wall-clock sums within each arm's recorded execution order, not a throughput benchmark.

The highest cost is prompt repetition: the strict planner and plan-to-test calls repeatedly include the target context. This is an engineering cost, not evidence of better trigger quality.

## Conclusion

The C2 gain in hypothesis-level coverage survives equal generated-test budget (4/5 versus 3/5), but not efficiency normalization. It is therefore a coverage/diversity gain with a per-candidate efficiency penalty, not a clear overall trigger-quality win.
