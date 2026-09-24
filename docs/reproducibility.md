# Reproducibility

## Clean installation and offline verification

From a fresh checkout:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m compileall scripts tests
python -m pytest -q
python scripts/verify_core_results.py
python scripts/verify_experiment4_artifacts.py
replay --config configs/experiment4.json --artifacts artifacts/experiment4/iteration3 --arm C2
replay --config configs/experiment4.json --artifacts artifacts/experiment4/iteration3 --arm C1_BUDGETED
```

The core verifier reads and aggregates:

- `results/experiment2_replication2.csv`: the clean replication, two preserved five-attempt halves, ten attempts per condition.
- `results/experiment2_re_evaluated.csv`: cumulative evidence, 25 attempts per condition across the preserved batches.

It derives mechanism matches from `hypothesis_matches_true_failure_mechanism` and verified F2P from `verified_f2p`. It verifies the condition names, batch labels, required fields, and exact documented counts. It does not rerun generation or instantiate a provider.

The Experiment 4 verifier checks the frozen CSV hashes, evidence-bundle hashes, exact replay metrics, and generated report consistency:

```bash
python -m pytest -q tests/integration/test_golden_replay.py
replay --config configs/experiment4.json --artifacts artifacts/experiment4/iteration3 --arm C2
replay --config configs/experiment4.json --artifacts artifacts/experiment4/iteration3 --arm C1_BUDGETED
```

No `DEEPSEEK_API_KEY` is needed for these commands, no provider is constructed, and no target checkout is required by evidence replay.

## External harness

If `workspace/harness-pysnooper-buggy` and `workspace/harness-pysnooper-fixed` are present with their `env39` runtimes, run:

```bash
python scripts/verify_harness.py
```

The expected machine-readable result is `buggy=1` and `fixed=0`. The script also records execution logs and environment metadata under `artifacts/harness/`. If the preserved checkouts are absent, offline evidence verification remains valid and the external check is skipped.

## Provenance

Every new run records the config hash, source commit, prompt hashes, model configuration, visible input manifest, frozen-hypothesis hashes, plan hashes, test hashes, execution command/environment, token usage, and evaluator version. The JSONL ledger is ordered and append-only. A completed run requires a new run ID; resume mode refuses to overwrite completed evidence.

## Frozen Experiment 4 baseline integrity

The authoritative pre-refactor hashes are checked by `scripts/verify_experiment4_artifacts.py`:

- `results/experiment4_iteration3_raw.csv`: `6b5a316a26e044f640c76913b1dd78a2cd1a2b7092d97cc90ad198183c21efd8`
- `results/experiment4_iteration3_raw_budgeted.csv`: `6a21ff378b7ddcad3bbaccbce3bbda835520444a870b3cecc219356bae26959b`

The evidence bundles record these source hashes and contain immutable row snapshots derived from them. Replay validates the snapshots and manifests; it does not silently locate or re-aggregate an unrelated repository-level CSV.
