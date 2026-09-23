# Experiment 2 case study

## Selected transfer case

The evaluator retrospectively selected `PySnooper:1` and the two historical units `cookiecutter:1, PySnooper:3`. The strongest relationship is `cookiecutter:1`: its fix changes implicit `open(...)` decoding to explicit UTF-8 and adds a non-ASCII regression fixture. `PySnooper:3` is intentionally weaker: it is a public file-output path bug but its historical mechanism is a path-variable mismatch, not encoding. The subset was selected by mechanism/trigger/invariant compatibility, not lexical similarity.

This is a retrospectively selected transfer-feasibility experiment. It evaluates whether the mechanism can transfer when suitable history is available. It does not evaluate autonomous retrieval quality.

## Leakage boundary

Generation read only `data/experiment2_target_context/PySnooper-1.txt`, plus the raw or structured history file for B/C. The evaluator-only truth is `data/evaluator_truth/experiment2_PySnooper-1.json`; the fixed checkout and hidden regression are not read by `scripts/run_experiment2.py`.

## Representative structured attempt

Final C attempt 5 (`generated_tests/experiment2/PySnooper_1/C_attempt_5.py`) correctly identified the target-side source-decoding region and marked `cookiecutter:1` as supported. It generated a UTF-8 source-file probe with a meaningful assertion. The exact same test failed on both buggy and fixed revisions (`F2F`): the test re-decorated a module function in a way that did not isolate the fixed source-decoding behavior, and its expected source-line assertion was not satisfied on either revision. This is an oracle/test-construction failure, not F2P.

## Important exploratory signal

Before tightening the test contract, run-1 C attempt 1 generated a direct non-ASCII file-output probe grounded in `FileWriter.write`. The unchanged test failed on the buggy checkout with `UnicodeEncodeError` at `pysnooper/tracer.py:134` and passed on the fixed checkout. That is a strong exception-level mechanism signal, but it was not counted as F2P because the test let the expected target exception escape rather than failing at an intended assertion. The run-1 artifact and logs remain available for review; the final run required assertion-level handling equally across A/B/C.

## Evaluator-corrected conclusion from this case

The original strict evaluator treated target-origin exceptions as mechanical. Under the corrected evaluator, exploratory C attempts 1 and 5 are valid `EXCEPTION_F2P`: their stored pre-execution hypotheses and target-supported oracles predict locale-dependent encoding failure, the buggy tests raise `UnicodeEncodeError` in `pysnooper/tracer.py`, and the unchanged fixed tests pass. The new 10-attempt replication produced no additional F2P; C had 6/10 mechanism matches. Across 25 attempts per condition, C has 2 verified exception F2P and 15 mechanism matches; A and B have none. The evidence supports positive transfer feasibility in this selected case, not architecture proof or generalization.
