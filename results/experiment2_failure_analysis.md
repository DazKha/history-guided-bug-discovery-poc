# Experiment 2 failure analysis

The final run used five attempts per condition. Classification is based on unchanged generated tests executed on the verified buggy and fixed checkouts. `F2P` requires an assertion-level semantic failure on buggy and a pass on fixed; an unhandled target exception is not counted as a meaningful assertion failure.

Chosen target: `PySnooper:1`. Historical subset: `cookiecutter:1, PySnooper:3`.

## A — TARGET_ONLY

Attempts=5; tests=5; meaningful buggy failures=0; F2P=0; F2F=0; P2P=5; P2F=0; mechanical=0; model/no-support=0/0; mechanism-match=0; target-oracle-supported=5; repairs=0; LLM calls=5.

| Attempt | Status | Outcome | Mechanism match | Target oracle | Failure layer |
|---:|---|---|---|---|---|
| 1 | TEST | P2P | no | yes | HYPOTHESIS |
| 2 | TEST | P2P | no | yes | HYPOTHESIS |
| 3 | TEST | P2P | no | yes | HYPOTHESIS |
| 4 | TEST | P2P | no | yes | HYPOTHESIS |
| 5 | TEST | P2P | no | yes | HYPOTHESIS |

## B — NAIVE_RAW_HISTORY

Attempts=5; tests=4; meaningful buggy failures=0; F2P=0; F2F=0; P2P=4; P2F=0; mechanical=0; model/no-support=0/1; mechanism-match=0; target-oracle-supported=4; repairs=0; LLM calls=5.

| Attempt | Status | Outcome | Mechanism match | Target oracle | Failure layer |
|---:|---|---|---|---|---|
| 1 | TEST | P2P | no | yes | HYPOTHESIS |
| 2 | TEST | P2P | no | yes | HYPOTHESIS |
| 3 | MODEL_ERROR | MODEL_ERROR | no | no | TEST_GENERATION |
| 4 | TEST | P2P | no | yes | HYPOTHESIS |
| 5 | TEST | P2P | no | yes | HYPOTHESIS |

## C — STRUCTURED_APPLICABILITY_AWARE

Attempts=5; tests=3; meaningful buggy failures=1; F2P=0; F2F=1; P2P=2; P2F=0; mechanical=0; model/no-support=0/2; mechanism-match=2; target-oracle-supported=3; repairs=0; LLM calls=5.

| Attempt | Status | Outcome | Mechanism match | Target oracle | Failure layer |
|---:|---|---|---|---|---|
| 1 | MODEL_ERROR | MODEL_ERROR | no | no | TEST_GENERATION |
| 2 | MODEL_ERROR | MODEL_ERROR | no | no | TEST_GENERATION |
| 3 | TEST | P2P | no | yes | HYPOTHESIS |
| 4 | TEST | P2P | yes | yes | SEMANTIC_NON_TRIGGER |
| 5 | TEST | F2F | yes | yes | SEMANTIC_NON_TRIGGER |

## Layer interpretation

- A: all five executable tests were P2P; the model explored plausible state/tracing hypotheses but none matched the hidden encoding mechanism.
- B: four tests were generated and one attempt returned no JSON. The raw evidence did not produce an encoding-mechanism match; executable tests were P2P.
- C: two attempts returned no usable JSON, one weak-history hypothesis was P2P, one mechanism-matching source-decoding test was P2P, and one mechanism-matching test was F2F because its oracle failed on both revisions. This is transfer signal without verified discovery.
- The first exploratory generation pass is preserved under `artifacts/experiment2_llm_run1/` and `generated_tests/experiment2_run1/`. It produced two exception-level buggy failures with fixed passes for encoding hypotheses, but those were deliberately excluded from F2P because the tests did not turn the expected no-error property into an assertion.

No generated test in the final strict run achieved F2P. This is a negative result about this small feasibility run, not evidence that the target mechanism is absent: the evaluator-only target truth and the exception trace show the mechanism is real, while test/oracle construction remained the bottleneck.
