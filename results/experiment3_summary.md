# Experiment 3 summary

## Experiment 3A — natural end-to-end

The final parser-valid run used five fresh structured-history hypothesis calls. It produced 3 `NO_SUPPORTED_HYPOTHESIS` and 2 `MODEL_ERROR` responses; no direct or planned tests were generated. The earlier `live1` run is preserved but excluded because it exposed a parser contract bug that required `test_code` at the hypothesis-only stage.

## Experiment 3B — conditional trigger test

The five stored mechanism-matched hypotheses were kept verbatim. C1 generated one direct test per frozen hypothesis. C2 used one planner call followed by up to two bounded JSON-format repairs.

| Arm | Frozen hypotheses | Executable tests | Activated buggy tests | F2P | F2F | P2P | F2P / hypothesis | F2P / executed test |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| C1 direct | 5 | 5 | 3 | 2 | 1 | 2 | 2/5 = 40.0% | 2/5 = 40.0% |
| C2 planner | 5 | 8 | 6 | 3 | 3 | 2 | 2/5 = 40.0%* | 3/8 = 37.5% |

`*` C2’s hypothesis-normalized value counts hypotheses with at least one F2P; three of five hypotheses never produced a valid trigger plan after two repairs. C2’s three F2P rows came from two hypotheses.

## Trigger metrics

- Trigger executability: C1 5/5 direct tests; C2 8/8 generated tests. Planner completeness was 2/5 hypotheses.
- Trigger activation: C1 3/5 = 60.0%; C2 6/8 = 75.0% among executable tests.
- Diversity yield with verified F2P: 2/5 C2 hypotheses = 40.0%; C1 also had 2/5 hypotheses with F2P.
- C2 used 8 test pairs versus C1’s 5 pairs.
- C1 used 5 test-generation calls; C2 used 12 planner calls and 8 test-generation calls = 20 calls.
- Token totals are lower bounds because malformed planner responses from the first two passes were not logged with usage before the logging fix.

## Interpretation

C2 increased total F2P from 2 to 3 only while using 8 rather than 5 executed tests and 20 rather than 5 LLM calls. Hypothesis-normalized yield did not improve, and F2P per executed test decreased from 40.0% to 37.5%. This is CASE C: extra search found one additional F2P, but the data do not show a quality improvement after execution-budget normalization.

The dominant remaining failure is trigger-planner instantiation: 3/5 frozen hypotheses failed to yield valid structured triggers after two bounded JSON repairs. Among executable C2 tests, F2F remained common, so assertion/observable alignment is still unstable.
