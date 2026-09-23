# Experiment 3 budget analysis

## Observed budget

| Mode/arm | Hypotheses | Generated tests | Buggy/fixed pairs | LLM calls | Verified F2P |
|---|---:|---:|---:|---:|---:|
| natural hypothesis stage | 5 | 0 | 0 | 5 | 0 |
| conditional C1 direct | 5 | 5 | 5 | 5 | 2 |
| conditional C2 planner | 5 | 8 | 8 | 20 | 3 |

C2 used 12 planner calls and 8 test-generation calls. C1 used 5 direct test-generation calls. Each generated test was executed on both revisions; the table reports test pairs, so revision executions are twice those values.

## Normalized comparison

- F2P per hypothesis: C1 2/5 = 40.0%; C2 hypotheses with any F2P 2/5 = 40.0%.
- F2P per executed test: C1 2/5 = 40.0%; C2 3/8 = 37.5%.
- Executions per verified F2P: C1 5/2 = 2.5 test pairs; C2 8/3 = 2.67 test pairs.
- LLM calls per verified F2P: C1 5/2 = 2.5 known calls; C2 20/3 = 6.67 calls.
- Prompt/completion tokens are partial lower bounds because malformed planner responses from the first two passes lacked usage fields before the logging fix.

C2’s raw F2P count is higher, but its execution- and hypothesis-normalized yield is not. The evidence does not support a trigger-quality improvement beyond additional search budget.
