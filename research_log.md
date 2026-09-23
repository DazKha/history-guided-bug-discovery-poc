# Research log

## 2026-09-23 — benchmark and API verification

The official BugsInPy source was verified at [soarsmu/BugsInPy](https://github.com/soarsmu/BugsInPy). The checked-out benchmark revision is `11c5f1eea954a42132cfd06bf257766a7963e0fd`. Its README documents `bugsinpy-checkout`, `bugsinpy-compile`, and `bugsinpy-test`; the current Dockerfile uses Python 3.12.

Local toolchain observed:

- Python 3.13.5, Python 3.12.6, and Python 3.9.18 available
- Git 2.48.1
- Docker 27.0.3 installed, but the Docker daemon was not running
- pytest 9.0.3 on the host

DeepSeek API semantics were checked against the official [Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/) and [Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/) documentation. The experiment uses `deepseek-flash`, `https://api.deepseek.com/chat/completions`, JSON output, `thinking: {"type":"disabled"}`, temperature `0.2`, and max output `1800`. The API smoke call returned HTTP 200 with usage accounting. The key was read from the environment after parsing the local `.env`; it was never printed or written to an artifact.

## Harness investigation

Target: BugsInPy `PySnooper:1`.

- Buggy revision: `e21a31162f4c54be693d8ca8260e42393b39abd3`
- Fixed revision: `56f22f8ffe1c6b2be4d2cf3ad1987fdb66113da2`
- Benchmark regression test: `tests/test_chinese.py::test_chinese`
- Benchmark metadata Python version: `3.8.1`
- Host-compatible runtime used: Python `3.9.18` in an isolated `env39` virtual environment
- Runtime locale: `LC_ALL=C PYTHONUTF8=0 PYTHONCOERCECLOCALE=0`

Observed setup failures and resolutions:

1. Python 3.13 virtualenv lacked `setuptools`; the BugsInPy setup script imports it.
2. After installing setuptools, Python 3.13 failed at `from collections import Mapping`; this revision predates Python 3.10 compatibility.
3. Python 3.9 avoided that incompatibility, but the regression test required the historical `python_toolbox` test dependency; installing that dependency matched the upstream tox configuration.
4. Under the ASCII locale, the buggy regression test failed with the intended `UnicodeEncodeError` in `pysnooper.tracer.FileWriter.write`; the fixed regression test passed under the identical environment.

The exact stdout/stderr are in `artifacts/harness/buggy_regression.log` and `artifacts/harness/fixed_regression.log`; the version record is in `artifacts/harness/environment.json` and the machine-readable result is in `artifacts/harness/verification.json`.

## Data preparation

Historical pool: six real BugsInPy bugs from two projects:

`PySnooper:2`, `PySnooper:3`, `cookiecutter:1`, `cookiecutter:2`, `cookiecutter:3`, and `cookiecutter:4`.

Target: held-out `PySnooper:1`. Historical cases were retrospectively selected to test transfer feasibility; this experiment does not validate autonomous retrieval. Raw and structured JSON use the same six historical IDs. Structured fields carry direct/inferred provenance labels and repository evidence references.

The target context is generated from the buggy checkout only. It excludes the target regression test, BugsInPy metadata, fix metadata, generated setup artifacts, and evaluator-only truth. A post-generation check confirmed the target context did not contain `tests/test_chinese.py`, `fixed_commit_id`, or `bugsinpy_bug.info`.

## Final execution

The final study used five attempts per condition for one target, for fifteen condition/attempt cells, as required for the one-target initial run. Each call used the same DeepSeek model and output configuration; C was allowed to return `NO_SUPPORTED_HYPOTHESIS`. One mechanical response normalization was used for valid model responses that supplied a complete hypothesis but labeled the top-level status `SUPPORTED`; no test oracle was altered during evaluation.

Results are generated in `results/results.csv` and `results/summary.csv`. Execution logs are under `artifacts/execution_logs/PySnooper_1/`.

Final raw counts:

| Condition | Attempts | Tests generated | NO_SUPPORTED_HYPOTHESIS | F2P | P2P | F2F | P2F | Mechanical |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A target-only | 5 | 4 | 1 | 0 | 3 | 0 | 0 | 1 |
| B raw history | 5 | 0 | 5 | 0 | 0 | 0 | 0 | 0 |
| C structured/applicability-aware | 5 | 0 | 5 | 0 | 0 | 0 | 0 | 0 |

No generated test was an F2P discovery. The harness regression itself is a separate evaluator sanity check and is not counted as an LLM-generated discovery.

## Failure analysis

- A: four tests were generated; three passed on both revisions (`SEMANTIC_NON_TRIGGER`), one invalid watch-expression test raised `SyntaxError` on both revisions (`MECHANICAL_EXECUTION`), and one attempt abstained at the hypothesis layer.
- B: all five attempts returned no supported hypothesis after raw-history exposure; classified as `HISTORY_DISTRACTION` / hypothesis-layer non-discovery.
- C: all five attempts returned `NO_SUPPORTED_HYPOTHESIS` with `NOT_APPLICABLE`; classified as conservative `APPLICABILITY` rejection.

The small result does not establish superiority. It demonstrates that the real buggy/fixed harness, leakage-separated context, three-condition runner, and unchanged-test evaluator work, while this one-target run did not produce a verified generated discovery for any condition.

## 2026-09-23 — Experiment 1 audit and Experiment 2 transfer-feasibility rerun

The audit was completed before changing the first experiment. It found that the target was `PySnooper:1`, whose hidden defect is locale-dependent implicit encoding in `pysnooper/tracer.py`; `cookiecutter:1` was the only clearly strong transfer case in the original six-case pool. Experiment 1’s raw representation omitted `evidence.fix_diff`, B inherited the common abstention rule, C’s fields were generic, and the target locale facts were absent from the prompt. Evidence and conclusions are in `results/experiment1_audit.md`.

The evaluator then ranked transfer candidates by mechanism, trigger, invariant, and behavioral context. The chosen subset was `cookiecutter:1` plus the weaker same-domain `PySnooper:3`, recorded in `data/transfer_case_candidates.json`. The generation/evaluator boundary is recorded in `data/target_leakage_manifest.json`; `scripts/run_experiment2.py` does not import or read evaluator-only truth.

Experiment 2 used a bounded target context assembled from ordinary buggy-checkout source/docs/tests and visible runtime facts (`Python 3.9.18`, `LC_ALL=C`, `PYTHONUTF8=0`, `PYTHONCOERCECLOCALE=0`). B received full raw fix diffs/regression evidence. C received concise structured units with Context, Preconditions, Trigger, Expected Invariant, Observed Failure, Failure Mechanism, Oracle, Oracle Provenance, Test Strategy, Evidence References, and Confidence, plus an explicit SUPPORTED/WEAK/NOT_APPLICABLE applicability decision. The A/B/C prompt distinction is implemented in `scripts/run_experiment2.py`.

The first 15-call exploratory pass is preserved under `artifacts/experiment2_llm_run1/` and `generated_tests/experiment2_run1/`. It exposed an output-contract problem: two C encoding tests failed with the intended `UnicodeEncodeError` on buggy and passed on fixed, but did not fail at an assertion. The final 15-call pass added the same assertion-level exception-handling requirement to all conditions and was evaluated as the reported result. This change was applied uniformly before the final rerun; no test was edited after seeing its buggy/fixed outcome.

Final Experiment 2 raw counts: A had 5/5 tests, 0 mechanism matches, 0 F2P, 5 P2P; B had 4/5 tests, 0 mechanism matches, 0 F2P, 4 P2P, and one model/JSON error; C had 3/5 tests, 2 mechanism matches, 0 F2P, 2 P2P, 1 F2F, and two model/JSON errors. The final run made 15 DeepSeek calls, used 203,970 prompt tokens and 8,239 completion tokens where reported, and consumed approximately 64.8 seconds of generation wall time; B/F execution logs are under `artifacts/execution_logs/experiment2_PySnooper_1/`.

No final generated test achieved assertion-level F2P. The result is a negative discovery result with limited positive signal in C’s mechanism targeting, not evidence of architecture superiority. The remaining bottleneck is executable target-side oracle construction and robust test generation.

## 2026-09-23 — Exception-aware evaluator and controlled loop

The evaluator audit found a semantic undercount. `scripts/evaluate_generated_tests.py` classified any nonzero output without an assertion marker as mechanical, so a target-origin `UnicodeEncodeError` was excluded even when the model’s stored pre-execution hypothesis and oracle explicitly predicted locale-dependent encoding failure. The corrected criterion is: same unchanged test on buggy/fixed, meaningful semantic buggy failure, fixed pass, and a pre-execution supported oracle; meaningful failure is an assertion failure or a target exception violating that oracle. The full audit is in `results/evaluator_audit.md`.

All 30 preserved Experiment 2 artifacts were re-run unchanged. Two exploratory Condition C tests are valid `EXCEPTION_F2P`: both predict the FileWriter encoding invariant, fail at `pysnooper/tracer.py:134` with `UnicodeEncodeError` on buggy, and pass on fixed. They are not post-hoc oracles; the hypothesis and target evidence are in their stored model artifacts from before execution. No assertion F2P exists.

One additional uniform five-attempt batch per condition was run with the same model, target context, history, temperature, token budget, repair budget, and runtime. It produced no additional F2P. C had 3/5 mechanism matches, one F2F, and four P2P; A had 0/5 mechanism matches with four P2P and one model error; B had 1/5 mechanism match with four P2P and one model error.

Aggregate across 15 attempts per condition: A 0/15 verified F2P and 0 mechanism matches; B 0/15 verified F2P and 1 mechanism match; C 2/15 verified exception F2P and 9 mechanism matches. This is positive transfer-feasibility evidence in the retrospectively selected case, but not architecture proof: the verified cases occurred in one exploratory batch and did not reproduce in later batches. The remaining instability is trigger construction after mechanism identification.

## 2026-09-23 — Replication 2 under frozen protocol

The existing Experiment 2 protocol was inspected before generation. No target, context, history, prompt, model, parameters, evaluator, applicability logic, or repair policy was changed. The runner’s prompt contract is fixed at five attempts per invocation, so the replication work was executed in independent five-attempt halves. The first `loop1` half was already included in the preserved prior aggregate; the fresh replication halves for this turn are `replication2b` and `replication2c`.

Replication-only results: A had 10 attempts, 9 executable tests, 0 mechanism matches, 0 F2P, 7 P2P, 1 F2F, and 1 unsupported oracle; B had 10 attempts, 9 executable tests, 1 mechanism match, 0 F2P, 9 P2P, and 1 model error; C had 10 attempts, 5 mechanism matches, 10 executable tests, 0 F2P, 9 P2P, and 1 F2F. C mechanism-to-F2P conversion was `0/5 = 0%` in this replication batch.

Cumulative totals after the earlier `loop1` batch were 20 attempts per condition: A `0/20` verified F2P and `0/20` mechanism matches; B `0/20` verified F2P and `1/20` mechanism match; C `2/20` verified exception F2P and `11/20` mechanism matches. This intermediate total is retained as historical run accounting; the fresh replication results and final 25-attempt totals are recorded below.

No optional C1/C2 ablation was run because the frozen replication already answered the immediate robustness question and the user instruction was to avoid redesign during this batch. Proposed interventions are listed separately in `results/next_experiment_recommendations.md`.

## 2026-09-23 — Replication accounting correction

The prior `loop1` five-attempt batch was already part of the preserved 15-attempt Experiment 2 aggregate. It is therefore not counted as new replication work in this turn. The actual new replication consists of `replication2b` and `replication2c`, 10 fresh attempts per condition total. The frozen protocol and evaluator were unchanged; only re-evaluation/report bookkeeping was updated to preserve source-batch provenance and unique attempt IDs.

New replication results: A `0/10` F2P and `0/10` mechanism matches; B `0/10` F2P and `1/10` mechanism match; C `0/10` F2P and `6/10` mechanism matches, with 2 F2F and 8 P2P among C’s executable tests. C mechanism-to-F2P conversion was `0/6 = 0%`.

Cumulative results: 25 attempts per condition. A had `0/25` F2P and `0/25` mechanism matches; B had `0/25` F2P and `2/25` mechanism matches; C had `2/25` verified exception F2P and `15/25` mechanism matches. The two verified cases remain in the preserved exploratory C batch. This replication reproduced the mechanism-match advantage but not the F2P conversion.
