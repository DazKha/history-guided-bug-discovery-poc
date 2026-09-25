# History-Guided Bug Discovery PoC

This repository is an engineering proof of concept for one bounded slice of a history-guided bug-discovery system:

```text
historical evidence + buggy target context
        -> A/B/C hypothesis generation
        -> frozen hypotheses and candidate tests
        -> buggy/fixed differential execution
        -> preserved evidence and reports
```

It does not implement autonomous history retrieval, learned memory updates, or a general multi-repository benchmark. The selected target is `PySnooper:1`; the selected historical inputs are `cookiecutter:1` and `PySnooper:3`. Historical selection was retrospective to test transfer feasibility.

## Quickstart

From a fresh clone:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest -q
python scripts/verify_core_results.py
python scripts/verify_experiment4_artifacts.py
replay --config configs/experiment4.json --artifacts artifacts/experiment4/iteration3 --arm C2
replay --config configs/experiment4.json --artifacts artifacts/experiment4/iteration3 --arm C1_BUDGETED
```

These checks are offline. They read committed evidence and do not call an LLM; no API key or target checkout is needed. The two `replay` commands verify preserved downstream Experiment 4 evidence and also do not call the model.

To inspect the current Experiment 2 prompt without making a model call:

```bash
python scripts/render_experiment2_prompt.py --condition C --attempt 1
```

To start a new A/B/C Experiment 2 generation run, use a new run label:

```bash
DEEPSEEK_API_KEY=... python scripts/run_experiment2.py --run-label reviewer-20260925 --attempts 5
```

This command is a live generation run, not part of offline verification. It requires `DEEPSEEK_API_KEY`, calls the configured DeepSeek model, and refuses to reuse an existing output location.

The packaged command below is a different downstream pipeline. It loads frozen hypotheses and runs Trigger Plan/test generation; it is not the Experiment 2 A/B/C reproduction command:

```bash
DEEPSEEK_API_KEY=... run --config configs/experiment4.json --arm C2
```

It additionally requires the configured external buggy/fixed target checkouts and Python 3.9 runtime. The committed checkout does not contain those external targets, so this live command was not run during the refactor.

The external harness check is separate:

```bash
python scripts/verify_harness.py
```

It requires `workspace/harness-pysnooper-buggy/PySnooper` and `workspace/harness-pysnooper-fixed/PySnooper`, each with the documented `env39` runtime. Those checkouts are absent from this public clone.

## What A/B/C compares

The clean preserved comparison has 10 attempts per condition. One attempt is one hypothesis-generation call, not one target bug and not necessarily one executable test.

| Condition | Agent-visible input | Existing v1 rule-based mechanism-related signal | Attempts | Verified F2P |
| --- | --- | ---: | ---: | ---: |
| A `TARGET_ONLY` | target context only | 0 | 10 | 0 |
| B `NAIVE_RAW_HISTORY` | target context + raw history | 1 | 10 | 0 |
| C `STRUCTURED_APPLICABILITY_AWARE` | target context + structured history + applicability-aware instructions | 6 | 10 | 0 |

In compact form, the preserved v1 signal is A `0/10`, B `1/10`, C `6/10`.

These are the unchanged historical v1 counts from `results/experiment2_replication2.csv`. The existing signal is not six independently validated, fully mechanism-aligned hypotheses: `scripts/evaluate_experiment2.py` checks for at least one encoding-related token and at least one target-related token across hypothesis, trigger, failure, test, and oracle text. It is a broad rule-based mechanism-related signal. Verified F2P is the stronger downstream result and is zero in this clean replication.

Condition C therefore changes both the history representation and the instructions: it supplies structured failure knowledge and asks for bounded `SUPPORTED`, `WEAK`, or `NOT_APPLICABLE` applicability decisions. The result should not be attributed to data formatting alone.

## Inspect one hypothesis through its result

The preserved conditional hypothesis `conditional-h01` can be followed from source to downstream result with standard tools:

```bash
jq '.[] | select(.hypothesis_id == "conditional-h01")' data/experiment3_conditional_hypotheses.json
jq '.' artifacts/experiment4/iteration3/hypotheses/conditional-h01-e0c8bd3ab2.json
jq '.' artifacts/experiment4/iteration3/C2/conditional-h01-e0c8bd3ab2__plan-1.json
rg 'conditional-h01-e0c8bd3ab2' artifacts/experiment4/iteration3/C2/evidence-rows.csv
```

The first file is the frozen hypothesis source, the second is the Experiment 4 copy, the third is one Trigger Plan/test candidate, and the CSV row contains the replayable buggy/fixed classification. The corresponding preserved generated test and execution logs are referenced by the artifact/evidence records.

## Where the important pieces live

- `scripts/run_experiment2.py`: actual A/B/C generation runner and executable prompt construction.
- `scripts/render_experiment2_prompt.py`: read-only current-code prompt renderer and SHA-256 printer.
- `scripts/run_experiment.py`: older generation runner retained for historical provenance; it is not the clean current runner.
- `data/experiment2_target_context/PySnooper-1.txt`: shared target context.
- `data/experiment2_historical_raw.json`: B's historical input.
- `data/experiment2_historical_structured.json`: C's structured historical input.
- `artifacts/experiment2_llm/PySnooper_1/`: preserved Experiment 2 model outputs.
- `generated_tests/experiment2/PySnooper_1/`: preserved Experiment 2 generated tests.
- `results/experiment2_replication2.csv`: authoritative clean A/B/C result table.
- `scripts/verify_core_results.py`: offline verifier for the A/B/C CSVs.
- `configs/experiment4.json`: downstream Trigger Plan/test-generation configuration.
- `data/experiment3_conditional_hypotheses.json`: frozen downstream hypotheses.
- `artifacts/experiment4/iteration3/`: preserved downstream artifact/evidence bundles.
- `src/history_guided_bug_discovery/application/prompts.py`: downstream Trigger Plan and test-generation prompts.
- `docs/code-map.md`: stage-by-stage and condition-by-condition traceability map.

There are no standalone executable Experiment 2 prompt files: the current runner is the source of truth. The removed `prompts/experiment2_*.md` files were pointer-only and unused; the small `prompts/*.txt` files are legacy prompt fragments retained for provenance, and neither set is the source used by the current Experiment 2 runner.

## Limitations

- The target set is one selected BugsInPy target and the historical cases were selected retrospectively.
- Structured history is prepared data, not learned memory or autonomous retrieval.
- The v1 mechanism signal is rule-based and broad; it does not validate a complete causal explanation.
- The clean A/B/C replication produced no verified F2P. Plausible hypotheses can still fail during trigger construction, assertion design, or execution setup.
- Live generation and the external harness require an API key and/or external target checkouts that are not part of this public clone.

## Detailed documentation

- [Code and prompt map](docs/code-map.md)
- [Architecture and implementation boundary](docs/architecture.md)
- [Reproducibility and provenance](docs/reproducibility.md)
- [Experiment 4 replay report](docs/experiment4-report.md)
- [Artifact schema](docs/artifact-schema.md)
- [Engineering results](docs/engineering-results.md)
- [Research log](research_log.md)
