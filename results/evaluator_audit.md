# Evaluator semantics audit

## Scope

This audit inspected the existing Experiment 2 evaluator (`scripts/evaluate_experiment2.py`), the preserved final artifacts under `artifacts/experiment2_llm/`, the preserved exploratory artifacts under `artifacts/experiment2_llm_run1/`, all generated tests, the buggy/fixed execution logs, the applicability decisions, and the pre-execution hypothesis/oracle JSON.

## Existing classification problem

The original evaluator imported `classify_output()` from `scripts/evaluate_generated_tests.py`. That classifier returned `FAIL` only when output contained an assertion marker. A target-origin exception such as `UnicodeEncodeError` was otherwise classified as `MECHANICAL_FAILURE`. `classify_pair()` then converted the pair to `MECHANICAL_FAILURE` before considering whether the exception was the behavior predicted by the hypothesis.

That rule is too narrow for proactive bug tests. A valid test can assert a no-error or output-preservation invariant by executing a public API; if the buggy target raises an unexpected target exception at the predicted operation and the unchanged test passes on the fixed revision, the exception is meaningful semantic evidence even if the generated test did not catch it and convert it into `AssertionError`.

The corrected evaluator therefore distinguishes:

- `ASSERTION_FAILURE`: an assertion-level failure in the intended generated test, with valid setup and a supported pre-execution oracle.
- `TARGET_EXCEPTION`: an exception raised inside target behavior, not generated setup, relevant to the pre-execution hypothesis/oracle.
- `MECHANICAL_FAILURE`: syntax/import/dependency/fixture/setup/timeout/harness failures, artificial failures, or unrelated exceptions.

The verified criterion is:

```text
verified_f2p =
    same unchanged test on buggy and fixed
    AND buggy has a meaningful semantic failure
    AND fixed passes
    AND the oracle was supported before execution

meaningful semantic failure = ASSERTION_FAILURE OR TARGET_EXCEPTION_VIOLATING_ORACLE
```

## Existing Unicode case

Exploratory structured attempt `C_attempt_1` is a valid exception-based F2P under this rule:

1. The generated test setup creates a temporary path, uses the public `pysnooper.snoop(path)` API, and supplies non-ASCII data. It is executable and does not inspect benchmark metadata or the fixed checkout.
2. Its pre-execution hypothesis explicitly predicts that `FileWriter.write` uses implicit locale encoding and may raise `UnicodeEncodeError`.
3. Its pre-execution oracle explicitly requires the trace to preserve non-ASCII values independently of locale and cites target `FileWriter.write`, `get_write_function`, README, and ordinary tests.
4. The buggy traceback reaches `pysnooper/tracer.py:134` and raises `UnicodeEncodeError` while writing the intended trace value.
5. The exact unchanged test passes on the fixed checkout.

This is therefore `EXCEPTION_F2P`, not a mechanical failure and not a post-hoc oracle. It was previously excluded only because the old evaluator required an assertion marker.

The final strict `C_attempt_5` is not F2P: its source-decoding hypothesis is mechanism-aligned, but the same assertion fails on both buggy and fixed revisions (`F2F`). Other generated exceptions that occur on both revisions, or arise from the test's fake stderr setup rather than the target defect, remain non-F2P.

## Re-evaluation policy

Every preserved generated test is re-run unchanged on both checkouts. The re-evaluator records the original hypothesis, oracle, applicability decision, oracle support status, execution pair, exception/assertion type, target relevance, same-test hash, and final classification. It never uses the hidden target truth to rewrite a model oracle; hidden truth is used only for the separate mechanism-match label.

The corrected evaluator is `scripts/re_evaluate_experiment2.py`. Its outputs are `results/experiment2_re_evaluated.csv` and `results/experiment2_re_evaluated_summary.md`.
