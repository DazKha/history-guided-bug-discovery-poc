# Experiment 5A — second-target end-to-end replication

Target: `tornado:1` (BugsInPy), buggy `6a5a0bfa370b6c0d3dbbf9589a560a98202d2baa`, fixed `4677c54cc18bbfbdf0f4dadf11610fab6203fd63`.

The independent evaluator-only Tornado probe failed on buggy and passed on fixed. The probe used the public WebSocket API and was not supplied to generation. The generated-test evaluator semantics were unchanged: supported pre-execution oracle, same unchanged test on both revisions, meaningful semantic buggy failure, and fixed pass are required for F2P. Test execution used the target-compatible `unittest` runner for generated `TestCase` classes and pytest otherwise; the runner choice is logged per test.

## Exact counts

| Condition | Attempts | Supported hypotheses | Mechanism matches | Executable tests | Semantic failures on buggy | F2P | F2F | P2P | Mechanical executions | Model/no-hypothesis failures | Mechanism-match rate | F2P rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A target only | 10 | 7 | 0 | 10 | 1 | 0 | 1 | 6 | 0 | 0 | 0.0% | 0.0% |
| B raw history | 10 | 4 | 0 | 7 | 1 | 0 | 1 | 3 | 3 | 3 | 0.0% | 0.0% |
| C structured history | 10 | 9 | 0 | 10 | 0 | 0 | 0 | 8 | 1 | 0 | 0.0% | 0.0% |

The `mechanical executions` column counts a mechanical buggy or fixed run directly from the state fields. Three B rows are also classified as `UNSUPPORTED_ORACLE` because the unchanged evaluator applies oracle support before pair classification; their raw logs remain preserved. C has one mechanical run caused by a generated subprocess command that treated `python -m unittest` as a filename.

## Interpretation

Structured history did not reproduce the Experiment 2 mechanism-identification signal on this second target: C produced 0/10 mechanism matches, equal to A and B. C's outputs frequently followed the historical encoding/environment pattern or unrelated Tornado behaviors, but did not identify the WebSocket lifecycle receiver mismatch.

Experiment 5B was not run beyond selection. Evaluator-only selection found 0 eligible C hypotheses (supported oracle plus mechanism match), so the prescribed conditional sample was underpowered and no hypothesis was synthesized, rewritten, topped up, or sent to the planner. See `experiment5_conditional_summary.md`.

This is CASE 2 for mechanism transfer. It is not evidence that the planner failed on this target because no valid frozen C hypothesis existed to test.
