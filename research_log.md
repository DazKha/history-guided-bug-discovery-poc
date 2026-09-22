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
