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

Typed domain models flow through application services using protocol ports.
Adapters isolate DeepSeek, BugsInPy checkouts, subprocess execution, the shared
benchmark evaluator, and append-only JSONL artifacts. See
[`docs/architecture.md`](docs/architecture.md).

The product discovery boundary uses `FindingValidator`; the empirical
`BenchmarkEvaluator` is the only component allowed to compare buggy and fixed
revisions.

## Repository structure

```text
src/history_guided_bug_discovery/  domain, config, ports, adapters, pipeline, reporting, CLI
configs/                            versioned run configuration
data/                               generation inputs and evaluator-only manifests
artifacts/                          preserved runs and execution evidence
generated_tests/                    preserved generated test source
results/                            historical CSVs and research reports
tests/unit, tests/contract, tests/integration/
```

## Quick start

Install the already-used test dependencies, then run the local suite:

```bash
python3 -m pytest -q
python3 -m compileall -q src scripts tests
```

A live run requires `DEEPSEEK_API_KEY` in the shell and never writes or prints
that secret:

```bash
python3 -m history_guided_bug_discovery.cli.run \
  --config configs/experiment4.json \
  --arm C2
```

The compatibility entry point remains available:

```bash
python3 scripts/run_experiment4.py --iteration 3 --arm C2
```

## Offline replay and reports

Replay requires no API key and reads the preserved machine-readable iteration-3
artifacts:

```bash
python3 -m history_guided_bug_discovery.cli.replay \
  --config configs/experiment4.json \
  --artifacts artifacts/experiment4/iteration3 \
  --arm C2

python3 -m history_guided_bug_discovery.cli.report \
  --config configs/experiment4.json \
  --run-id experiment4-final \
  --artifacts artifacts/experiment4/iteration3 \
  --arm C2
```

The report command writes consistent CSV, JSON, and Markdown summaries under
`artifacts/reports/`. `scripts/evaluate_experiment4.py` remains a replay wrapper
for historical command compatibility.

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
