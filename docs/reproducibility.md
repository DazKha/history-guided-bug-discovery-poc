# Reproducibility

## Offline verification

The golden replay uses only checked-in Experiment 4 iteration-3 rows and
preserved artifacts:

```bash
python3 -m pytest -q tests/integration/test_golden_replay.py
python3 -m history_guided_bug_discovery.cli.replay --config configs/experiment4.json --artifacts artifacts/experiment4/iteration3 --arm C2
python3 -m history_guided_bug_discovery.cli.replay --config configs/experiment4.json --artifacts artifacts/experiment4/iteration3 --arm C1_BUDGETED
```

No `DEEPSEEK_API_KEY` is needed and no provider is constructed by replay or
reporting.

## Provenance

Every new run records the config hash, source commit, prompt hashes, model
configuration, visible input manifest, frozen-hypothesis hashes, plan hashes,
test hashes, execution command/environment, token usage, and evaluator version.
The JSONL ledger is ordered and append-only. A completed run requires a new run
ID; resume mode refuses to overwrite completed evidence.

## Frozen baseline integrity

The pre-refactor authoritative hashes were:

- `results/experiment4_iteration3_raw.csv`: `6b5a316a26e044f640c76913b1dd78a2cd1a2b7092d97cc90ad198183c21efd8`
- `results/experiment4_iteration3_raw_budgeted.csv`: `6a21ff378b7ddcad3bbaccbce3bbda835520444a870b3cecc219356bae26959b`

The refactor replays these files without editing them.

## External harness

If `workspace/harness-pysnooper-buggy` and `workspace/harness-pysnooper-fixed`
are present, the benchmark harness check can run. Offline replay does not
require those checkouts. If absent, the external check is reported as skipped;
no result is synthesized.
