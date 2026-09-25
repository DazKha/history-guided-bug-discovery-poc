# Documentation and evidence index

Use this page to choose the smallest artifact that answers a review question. All paths are relative to the repository root.

## Start here

- **Main engineering report:** [`docs/engineering-results.md`](engineering-results.md) explains the recorded A/B/C comparison, the v1 mechanism-related signal, the clean replication, and the separate downstream Trigger Plan work.
- **Short outcome report:** [`FOLLOWUP_REPORT.md`](../FOLLOWUP_REPORT.md) is the concise required-output summary.
- **Code and prompt traceability:** [`docs/code-map.md`](code-map.md) maps inputs, prompt assembly, artifact paths, evaluators, and replay.

## Canonical clean Experiment 2 evidence

- **Canonical aggregate:** [`results/experiment2_replication2.csv`](../results/experiment2_replication2.csv) contains the clean 10-attempt-per-condition comparison: A `0/10`, B `1/10`, C `6/10` under the v1 mechanism-related signal, with zero verified F2P in every condition.
- **Offline verifier:** [`scripts/verify_core_results.py`](../scripts/verify_core_results.py) checks the canonical clean CSV and the 25-attempt cumulative CSV without an API key or model call.
- **Preserved generation artifacts:** `artifacts/experiment2_llm_replication2b/` and `artifacts/experiment2_llm_replication2c/` contain the recorded model responses; the matching generated tests are under `generated_tests/experiment2_replication2b/` and `generated_tests/experiment2_replication2c/`.
- **Execution evidence:** matching buggy/fixed logs are under `artifacts/execution_logs/experiment2_re_evaluated/replication2b/` and `replication2c/`.
- **Inputs and leakage boundary:** [`data/experiment2_target_context/PySnooper-1.txt`](../data/experiment2_target_context/PySnooper-1.txt), [`data/experiment2_historical_raw.json`](../data/experiment2_historical_raw.json), [`data/experiment2_historical_structured.json`](../data/experiment2_historical_structured.json), and [`data/target_leakage_manifest.json`](../data/target_leakage_manifest.json).

## Separate downstream Experiment 4 evidence

- **Report:** [`docs/experiment4-report.md`](experiment4-report.md).
- **Replay bundle:** `artifacts/experiment4/iteration3/`, with separate `C2/` and `C1_BUDGETED/` evidence bundles.
- **Frozen downstream hypotheses:** [`data/experiment3_conditional_hypotheses.json`](../data/experiment3_conditional_hypotheses.json) and `artifacts/experiment4/iteration3/hypotheses/`.
- **Raw baseline CSVs and hashes:** [`results/experiment4_iteration3_raw.csv`](../results/experiment4_iteration3_raw.csv) and [`results/experiment4_iteration3_raw_budgeted.csv`](../results/experiment4_iteration3_raw_budgeted.csv).
- **Offline checks:** [`scripts/verify_experiment4_artifacts.py`](../scripts/verify_experiment4_artifacts.py) and these commands:

  ```bash
  replay --config configs/experiment4.json --artifacts artifacts/experiment4/iteration3 --arm C2
  replay --config configs/experiment4.json --artifacts artifacts/experiment4/iteration3 --arm C1_BUDGETED
  ```

Experiment 4 is a separate downstream comparison over frozen hypotheses. Its F2P counts must not be read as a rerun of the clean Experiment 2 A/B/C generation comparison.

## Older provenance

These files explain earlier iterations and failure modes without changing the canonical result:

- [`results/experiment2_failure_analysis.md`](../results/experiment2_failure_analysis.md)
- [`results/experiment3_failure_analysis.md`](../results/experiment3_failure_analysis.md)
- [`results/experiment4_iteration_log.md`](../results/experiment4_iteration_log.md)
- [`results/experiment4_failure_analysis.md`](../results/experiment4_failure_analysis.md)
- [`research_log.md`](../research_log.md)
