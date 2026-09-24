# History-Guided Bug Discovery Engine

This repository is an engineering-oriented system for turning structured
historical bug evidence into executable, reproducible bug-discovery candidates.
It keeps generation, target execution, benchmark validation, and reporting
separate so an experiment can be replayed without an LLM call.

## Problem statement

The system tests whether a frozen mechanism hypothesis can be instantiated as a
deterministic test against a buggy target revision and pass unchanged on the
fixed revision. The strongest benchmark signal is F2P: meaningful failure on
buggy and pass on fixed. Historical evidence guides the hypothesis but does not
give generation access to evaluator-only truth.

## Architecture

The versioned `RunConfig` feeds a typed `DiscoveryPipeline`. Application
services build frozen hypotheses, optional strict trigger plans, and generated
tests through ports. Adapters isolate the configured model provider, target
checkout, subprocess executor, benchmark evaluator, and append-only JSON
ledger. See [`docs/architecture.md`](docs/architecture.md).

The product discovery boundary uses `FindingValidator`; the empirical
`BenchmarkEvaluator` is the only component allowed to compare buggy and fixed
revisions.

## Installation

The supported clean environment is Python 3.11 or newer:

```text
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m compileall -q src scripts tests
python -m pytest -q
```

The package declares `requests` as a runtime dependency and `pytest` in its
development extra. The installed console scripts are `run`, `replay`,
`evaluate`, and `report`.

## Offline verification

Offline replay reads only the supplied Experiment 4 evidence bundle. It does
not read a repository-level `results/` directory, instantiate a provider, need
`DEEPSEEK_API_KEY`, or execute a target checkout:

```bash
replay --config "$PWD/configs/experiment4.json" --artifacts "$PWD/artifacts/experiment4/iteration3" --arm C2
replay --config "$PWD/configs/experiment4.json" --artifacts "$PWD/artifacts/experiment4/iteration3" --arm C1_BUDGETED
python scripts/verify_experiment4_artifacts.py
```

The deterministic verifier checks the two frozen CSV hashes, required files,
exact replay metrics, evidence-bundle hashes, and generated report consistency.

## CLI modes

A live discovery run is the only mode that constructs the configured model
provider and requires `DEEPSEEK_API_KEY`; it never writes or prints the secret:

```bash
run \
  --config configs/experiment4.json \
  --arm C2
```

The compatibility entry point remains available:

```bash
python3 scripts/run_experiment4.py --iteration 3 --arm C2
```

`replay` validates and aggregates preserved machine-readable evidence.
`evaluate` runs replay aggregation for one or more arms. `report` writes a
JSON/CSV/Markdown report from the same replay result. These three modes never
construct a model provider.

```bash
report \
  --config configs/experiment4.json \
  --run-id experiment4-final \
  --artifacts artifacts/experiment4/iteration3 \
  --arm C2
```

The report command writes consistent CSV, JSON, and Markdown summaries under
`artifacts/reports/`. `scripts/evaluate_experiment4.py` remains a replay wrapper
for command compatibility.

## Repository structure

```text
src/history_guided_bug_discovery/  domain, config, ports, adapters, pipeline, reporting, CLI
configs/                            versioned run configuration
data/                               generation inputs and evaluator-only manifests
artifacts/                          preserved runs, bundles, and execution evidence
generated_tests/                    preserved generated test source
results/                            authoritative CSVs and research reports
tests/unit, tests/contract, tests/integration/
```

## Safety and leakage boundary

Generation sees only the target context, structured history, frozen hypothesis,
and validated trigger plan. It cannot receive fixed source, issue reports,
patches, hidden regression tests, evaluator verdicts, or benchmark paths.
Preflight rejects syntax errors, missing assertions, unconditional failure,
hidden benchmark access, Git inspection, and shell-based hidden-history access.

## Configuration and extension points

`configs/experiment4.json` versions the model, planner budget, execution
environment, paths, target adapter settings, and evaluator version. Add a new
LLM provider by implementing `LLMProvider`; add a target through
`TargetAdapter`; add an executor or evaluator by implementing its protocol.
The pipeline does not depend on a particular provider or target checkout path.

## Experiment 4 evidence

The preserved final C2 run has five frozen hypotheses, 15 candidate slots, 13
generated/executed tests, five F2P tests, four hypotheses with at least one F2P,
three P2P, five mechanical failures, two model-output failures, zero final C2
F2F, 21 LLM calls, and 326,930 recorded tokens. The budget-matched direct arm
has 15 slots, 13 generated tests, six F2P, three covered hypotheses, two F2F,
five P2P, two model-output failures, 15 calls, and 15,801 tokens.

The supported interpretation is directional and limited to one selected target:
structured history improved mechanism targeting in the selected case; strict
planning improved plan validity and hypothesis-level coverage; direct generation
remained more efficient per candidate. This is a CASE B / mixed result, not an
architecture proof or cross-project generalization claim. See
[`docs/experiment4-report.md`](docs/experiment4-report.md).

## Limitations

The benchmark evidence is small, target-specific, and dependent on generated
test quality. A valid plan is not a semantic proof, and the current system still
has mechanical/runtime failure modes. The benchmark checkout is optional for
offline replay; when absent, live target execution checks are skipped rather
than fabricating results.
