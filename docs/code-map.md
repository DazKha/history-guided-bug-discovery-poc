# Reviewer code and prompt map

This map distinguishes the current Experiment 2 A/B/C generation path from the later downstream Trigger Plan pipeline. Paths are relative to the repository root.

## Experiment 2 A/B/C generation

| Stage / condition | Entry point and prompt construction | Allowed inputs | Output artifacts | Evaluation / result path |
| --- | --- | --- | --- | --- |
| Shared target context | `scripts/run_experiment2.py` → `main()` → `base_instructions()` and `prompt_for()` | `data/experiment2_target_context/PySnooper-1.txt` | One JSON record and optional generated test per attempt | `scripts/evaluate_experiment2.py` can evaluate live-run artifacts when external checkouts exist |
| A `TARGET_ONLY` | `prompt_for("A", ...)` appends `NO HISTORICAL EVIDENCE` and target-only guidance | Shared target context only | `artifacts/experiment2_llm_<run-label>/PySnooper_1/A_attempt_N.json`; tests under `generated_tests/experiment2_<run-label>/PySnooper_1/` | Historical clean counts are verified from `results/experiment2_replication2.csv` by `scripts/verify_core_results.py` |
| B `NAIVE_RAW_HISTORY` | `prompt_for("B", ...)` appends raw evidence and explicitly says not to apply an applicability gate | Shared target context + `data/experiment2_historical_raw.json` | Same per-run paths with `B_attempt_N` | Same preserved CSV verifier; live evaluation uses `scripts/evaluate_experiment2.py` |
| C `STRUCTURED_APPLICABILITY_AWARE` | `prompt_for("C", ...)` appends structured evidence and instructions to decide `SUPPORTED`, `WEAK`, or `NOT_APPLICABLE` | Shared target context + `data/experiment2_historical_structured.json` | Same per-run paths with `C_attempt_N` | Same preserved CSV verifier; live evaluation uses `scripts/evaluate_experiment2.py` |

`base_instructions()` contains the common schema, leakage rules, test constraints, and oracle requirements. `prompt_for()` is the condition-specific assembly point. The renderer `scripts/render_experiment2_prompt.py` calls this same function and prints the current committed prompt plus its SHA-256 without constructing an LLM client or writing experiment artifacts. It identifies the output as current-code rendering; the repository does not prove that the exact historical request bytes were preserved.

The former `prompts/experiment2_*.md` files contained only condition labels and a pointer to `scripts/run_experiment2.py`. They were not read by the runner, reports, manifests, hashes, or replay commands, and were removed after the runner's redundant `write_templates()` side effect was removed. The legacy `prompts/target_only.txt`, `prompts/raw_history.txt`, and `prompts/structured_history.txt` files are preserved fragments and are not current runner inputs.

## Older Experiment 2 runner

`scripts/run_experiment.py` is an earlier runner. Its `prompt_for()` uses `data/target_context/PySnooper-1.txt`, `data/historical_raw.json`, and `data/historical_structured.json`, with a different response contract and artifact roots under `artifacts/llm/` and `generated_tests/`. It remains in the repository as historical provenance; it is not the command for reproducing the clean A/B/C result in the README.

## Downstream Experiment 4 pipeline

| Stage | Entry point / prompt | Inputs | Outputs | Offline path |
| --- | --- | --- | --- | --- |
| Load frozen hypotheses | `run --config configs/experiment4.json` → `DiscoveryPipeline.run()` | `data/experiment3_conditional_hypotheses.json`, structured history, target context, config | New run ledger under `artifacts/runs/<run_id>/` | Requires a live provider for new generation |
| Trigger Plan arm C2 | `src/history_guided_bug_discovery/application/prompts.py` → `strict_trigger_plan_v1()` and `plan_to_test_compact_v1()` | Frozen hypothesis, target context, structured history | Planner/test artifacts and execution events | Preserved artifacts are under `artifacts/experiment4/iteration3/C2/` |
| Direct arm C1 / C1_BUDGETED | `src/history_guided_bug_discovery/application/prompts.py` → `direct_test_v1()` | Frozen hypothesis and visible target context | Direct test artifacts and execution events | Preserved artifacts are under `artifacts/experiment4/iteration3/C1_BUDGETED/` |
| Differential evaluator | `src/history_guided_bug_discovery/adapters/benchmark_evaluator.py` | Same generated test on buggy and fixed checkouts | F2P/F2F/P2P/P2F and mechanical classifications | `ReplayPipeline` reads preserved evidence only |
| Preserved replay | `replay --config ... --artifacts artifacts/experiment4/iteration3 --arm ...` | Evidence bundle, config, frozen rows and hashes | Printed aggregate summary; no model call | `scripts/verify_experiment4_artifacts.py` checks hashes, metrics, and report consistency |

The packaged `run` command is therefore a downstream frozen-hypothesis pipeline, not an Experiment 2 A/B/C reproduction command. The `replay` command does not regenerate hypotheses, call the model, or rerun the external target.

## v1 result boundary

`scripts/evaluate_experiment2.py::mechanism_match()` is the implementation behind the preserved v1 mechanism-related signal. It searches combined hypothesis, trigger, potential-failure, test, and oracle text for one token from an encoding set (`utf-8`, `encoding`, `unicode`, `locale`, and similar) and one token from a target set (`pysnooper`, `trace`, `filewriter`, `tracer.py`, and similar). It does not independently validate every causal component of the reference mechanism. `scripts/verify_core_results.py` reads the already-recorded boolean column and confirms the preserved counts; it does not rerun the model or recreate the historical API calls.
