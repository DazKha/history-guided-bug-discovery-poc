# History-guided proactive bug discovery — empirical PoC

## Research question

Given the same target repository and LLM budget, does structured historical bug knowledge with applicability filtering produce more grounded and verifiable discoveries than target-only exploration or raw historical bug evidence?

## Experiment 1 (original run, now audited)

This PoC used the official [BugsInPy repository](https://github.com/soarsmu/BugsInPy), one held-out real target (`PySnooper:1`), and six historical bugs from two projects. The target’s real buggy/fixed revisions were executed before the LLM study. The final matrix had five attempts for each of:

- A — target-only context
- B — the same target context plus raw historical evidence
- C — the same target context plus the same historical IDs represented as structured Bug Knowledge Units and bounded applicability decisions

Historical cases were retrospectively selected to test transfer feasibility; this experiment does not validate autonomous retrieval. The original run is retained as the frozen baseline and is audited in `results/experiment1_audit.md`.

## Harness evidence

The target buggy commit is `e21a31162f4c54be693d8ca8260e42393b39abd3`; the fixed commit is `56f22f8ffe1c6b2be4d2cf3ad1987fdb66113da2`. The unmodified BugsInPy regression test failed on the buggy checkout and passed on the fixed checkout under the same Python 3.9.18 environment and ASCII locale. See `artifacts/harness/verification.json` and the two regression logs.

Python 3.13 was not usable for this historical revision because it removed `collections.Mapping`. Docker was installed but its daemon was unavailable, so the benchmark’s declared Python 3.8-era behavior was reproduced with the available local Python 3.9 runtime. This environment decision is documented in `research_log.md`.

## Leakage controls

For Experiment 1, generation saw only `data/target_context/PySnooper-1.txt` for the target. For Experiment 2, the stricter split is recorded in `data/target_leakage_manifest.json`: generation saw `data/experiment2_target_context/PySnooper-1.txt` and the selected history representation, while evaluator-only truth, the fixed checkout, target fix, and hidden regression remained separate under `data/evaluator_truth/` and the fixed workspace. Experiment 2 B/C share exactly `cookiecutter:1` and `PySnooper:3`.

The structured representation contains Context, Preconditions, Trigger, Expected Invariant, Observed Failure, Failure Mechanism, Oracle, Oracle Provenance, Test Strategy, Evidence References, and Confidence. Direct versus inferred provenance is recorded per field.

## DeepSeek configuration

The client follows the official [DeepSeek Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/) and disables default reasoning using the documented [Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/) switch. Configuration: model `deepseek-flash`, JSON output, `thinking.type=disabled`, temperature `0.2`, max output `1800` for Experiment 1 and `2200` for Experiment 2, bounded retries, and at most one repair attempt. API keys are read from `DEEPSEEK_API_KEY` and never logged.

## Experiment 1 results

| Condition | Attempts | Tests generated | No supported hypothesis | F2P | P2P | F2F | P2F | Mechanical |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A target-only | 5 | 4 | 1 | 0 | 3 | 0 | 0 | 1 |
| B raw history | 5 | 0 | 5 | 0 | 0 | 0 | 0 | 0 |
| C structured/applicability-aware | 5 | 0 | 5 | 0 | 0 | 0 | 0 | 0 |

The strongest success signal, F2P (meaningful FAIL on buggy and PASS on fixed), was zero for all three conditions. A produced four executable tests: three P2P non-triggers and one mechanical failure, plus one abstention. B produced no executable candidate. C conservatively rejected all five attempts as `NO_SUPPORTED_HYPOTHESIS` / `NOT_APPLICABLE`.

### Detailed generated case

In A/1, DeepSeek proposed that an invalid watched expression should be ignored and generated a real pytest. Both revisions raised `SyntaxError`, so the evaluator classified it mechanical and excluded it from discovery counts. A/2–A/4 were executable but passed on both revisions. The unchanged tests and logs are retained under `generated_tests/PySnooper_1/` and `artifacts/execution_logs/PySnooper_1/`.

The benchmark sanity test is intentionally separate: `tests/test_chinese.py::test_chinese` gives buggy FAIL/fixed PASS and proves the evaluator can observe a real revision-specific semantic difference. It is not counted as an LLM discovery because it is evaluator-only.

## Experiment 2: transfer-feasibility rerun

The audit found that Experiment 1 was not a clean transfer test: B did not receive the raw fix diff containing the strongest signal, B inherited C’s abstention instruction, C’s fields were generic, and target locale facts were omitted. Experiment 2 therefore used the smallest selected subset with one strong mechanism match (`cookiecutter:1`) and one weaker same-domain analogue (`PySnooper:3`). The evaluator selection is recorded in `data/transfer_case_candidates.json`.

This is a retrospectively selected transfer-feasibility experiment. It evaluates whether the mechanism can transfer when suitable history is available. It does not evaluate autonomous retrieval quality.

| Condition | Attempts | Hypotheses/tests | Mechanism matches | F2P | P2P | F2F | Mechanical | Model errors/no-support |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A target-only | 5 | 5/5 | 0 | 0 | 5 | 0 | 0 | 0/0 |
| B naive raw history | 5 | 4/4 | 0 | 0 | 4 | 0 | 0 | 1/0 |
| C structured + applicability | 5 | 3/3 | 2 | 0 | 2 | 1 | 0 | 2/0 |

No final generated test achieved F2P. C did produce more mechanism-aligned hypotheses, but its executable outputs were either P2P or F2F. An earlier exploratory pass produced a buggy-exception/fixed-pass encoding probe, but it was not counted because the expected target exception escaped instead of producing an assertion-level failure. That run is preserved under `artifacts/experiment2_llm_run1/`.

Detailed evidence is in [`results/experiment2_results.csv`](results/experiment2_results.csv), [`results/experiment2_failure_analysis.md`](results/experiment2_failure_analysis.md), [`results/experiment2_case_study.md`](results/experiment2_case_study.md), and [`results/experiment2_comparison_with_experiment1.md`](results/experiment2_comparison_with_experiment1.md).

### Evaluator correction and additional loop

The original strict evaluator was too narrow: it treated every non-assertion exception as mechanical. The corrected rule counts a failure as meaningful when it is either an assertion failure or a target-origin exception that violates an oracle recorded before execution, provided the unchanged test passes on fixed and setup is valid. The audit is in [`results/evaluator_audit.md`](results/evaluator_audit.md).

Re-evaluation of all 30 preserved Experiment 2 artifacts found two valid `EXCEPTION_F2P` cases in exploratory C. Both predict locale-dependent encoding failure, fail in target `pysnooper/tracer.py` with `UnicodeEncodeError` on buggy, and pass unchanged on fixed. No assertion-based F2P exists. A further uniform 5-attempt-per-condition loop produced no additional F2P; C still had 3/5 mechanism matches, one F2F, and four P2P.

Across 15 attempts per condition (exploratory, strict, and looped batches): A had 0/15 F2P and 0 mechanism matches; B had 0/15 F2P and 1 mechanism match; C had 2/15 verified exception F2P and 9 mechanism matches. This supports transfer feasibility in the selected case, but not architecture proof or generalization. See [`results/experiment2_re_evaluated.csv`](results/experiment2_re_evaluated.csv), [`results/experiment2_re_evaluated_summary.md`](results/experiment2_re_evaluated_summary.md), [`results/looped_experiment_results.csv`](results/looped_experiment_results.csv), and [`results/failure_analysis_final.md`](results/failure_analysis_final.md).

## Reproduction

From the repository root:

```bash
git clone https://github.com/soarsmu/BugsInPy vendor/BugsInPy
python3 -m scripts.bootstrap_benchmark
cd workspace/harness-pysnooper-buggy/PySnooper
/opt/anaconda3/bin/python3.9 -m venv env39
env39/bin/python -m pip install setuptools pytest python_toolbox
env39/bin/python setup.py install
cd ../../harness-pysnooper-fixed/PySnooper
/opt/anaconda3/bin/python3.9 -m venv env39
env39/bin/python -m pip install setuptools pytest python_toolbox
env39/bin/python setup.py install
cd ../../..
python3 -m scripts.verify_harness
python3 scripts/prepare_data.py
export DEEPSEEK_API_KEY='set this in your shell; do not write it to files'
python3 -m scripts.run_experiment --attempts 3 --conditions A,B,C
python3 -m scripts.evaluate_generated_tests

# Experiment 2 preparation, generation, and exact B/F evaluation
python3 scripts/prepare_experiment2.py
export DEEPSEEK_API_KEY='set this in your shell; do not write it to files'
python3 scripts/run_experiment2.py --attempts 5
python3 scripts/evaluate_experiment2.py
python3 scripts/write_experiment2_reports.py
python3 scripts/re_evaluate_experiment2.py --run all
python3 scripts/write_final_reports.py
```

The checked-in `data/`, `generated_tests/`, `artifacts/`, and `results/` files are the outputs from the completed runs. `data/case_manifest.json` describes Experiment 1; `data/target_leakage_manifest.json` describes the Experiment 2 agent/evaluator split and configuration. The API key is intentionally not part of the reproduction files.

## Limitations and conclusion

This is one target, 15 attempts per condition across three controlled batches, and a retrospective historical subset. It cannot support statistical significance, recall claims, or autonomous-retrieval claims. After correcting the evaluator, C produced two verified exception-based F2P tests in the preserved exploratory batch; A and B produced none. Later batches did not reproduce the F2P, so the stable conclusion is selected-case transfer feasibility with trigger-construction instability—not proof that the architecture works. The next study should add more held-out targets and pre-register retrieval.
