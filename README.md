# History-Guided Bug Discovery POC

This prototype tests a focused engineering question: does converting noisy historical bug reports into structured, mechanism-level knowledge help an agent target the right failure mechanism on a new target? The main contribution is the controlled comparison between target-only, raw-history, and structured-history prompting. Trigger Plans are a later engineering refinement for turning a correct hypothesis into an executable test.

## What this prototype demonstrates

The prototype uses a held-out BugsInPy `PySnooper:1` buggy/fixed revision pair and compares three conditions under the same target context, model/configuration, execution environment, evaluator policy, and comparable attempt budget:

| Condition | Mechanism matches | Attempts |
| --- | ---: | ---: |
| A — Target only | 0 | 10 |
| B — Target plus raw historical issue context | 1 | 10 |
| C — Target plus structured historical knowledge | 6 | 10 |

The clean replication produced zero F2P tests in all three conditions. In plain terms, structured history helped the agent focus on the correct bug mechanism, but it did not by itself solve executable trigger generation. The POC improved the reasoning/targeting stage and exposed a second engineering bottleneck.

The clean replication values above are derived from [`results/experiment2_replication2.csv`](results/experiment2_replication2.csv) by [`scripts/verify_core_results.py`](scripts/verify_core_results.py). The target is a selected transfer-feasibility case, and the historical cases were selected retrospectively; this is not a broad cross-project generalization study.

## Supporting cumulative evidence

The cumulative record combines 25 attempts per condition across the preserved exploratory, strict, loop, and replication batches:

| Condition | Mechanism matches | Attempts | Verified F2P |
| --- | ---: | ---: | ---: |
| A — Target only | 0 | 25 | 0 |
| B — Raw history | 2 | 25 | 0 |
| C — Structured history | 15 | 25 | 2 |

The two F2P results occurred in exploratory structured-history runs. They were verified against buggy and fixed revisions, but did not reproduce in the clean replication batch. They are evidence of feasibility, not a stable F2P improvement claim.

## Engineering diagnosis

The transfer path is:

```text
historical issue
    ↓
structured mechanism knowledge
    ↓
mechanism hypothesis
    ↓
concrete precondition / state / action / observable / assertion
    ↓
executable differential test
```

Structured history improved the mechanism-identification step. The remaining bottleneck was translating a correct mechanism hypothesis into a valid executable trigger and assertion that fails on the buggy revision and passes on the fixed revision.

## System pipeline

The proposed architecture is organized as Historical Knowledge Learning, Target Understanding, Knowledge Transfer / Hypothesis Generation, Executable Test Generation, and Differential Evaluation. The current POC implements bounded data preparation, leakage-separated target context, the A/B/C hypothesis prompts, direct test generation, strict plan validation, replayable artifacts, and the buggy/fixed evaluator. Autonomous retrieval, learned ranking, and a larger memory system remain future extensions. See [`docs/architecture.md`](docs/architecture.md).

## What improved

The central intervention is the structured-history representation. Raw issue history is reorganized into mechanism-oriented fields such as failure mechanism, preconditions, trigger, invariant, oracle provenance, and evidence references. A and B use the same selected historical cases as C where history is supplied; C adds an explicit applicability decision so the model can separate supported, weak, and not-applicable evidence.

## Remaining bottleneck

Mechanism identification is not equivalent to test construction. A hypothesis can name the right encoding, state, or sequencing failure and still produce a weak trigger, a wrong-shaped assertion, or a test that fails for setup reasons. F2P therefore remains a stricter downstream signal than a mechanism match.

## Engineering follow-up: validated Trigger Plans

Experiment 4 is a downstream implementation refinement, not the main project idea. It added a strict Trigger Plan contract, deterministic validation, and bounded repair inside executable-test generation. Valid plans improved from 2/5 hypotheses to 5/5. In the budget-matched comparison, hypotheses with at least one F2P improved from 3/5 for direct generation to 4/5 for the planner, while direct generation remained more efficient per generated test. The conclusion is that Trigger Plans improved reliability and hypothesis coverage, but did not improve per-test trigger efficiency. Details are in [`docs/experiment4-report.md`](docs/experiment4-report.md).

## Repository layout

```text
src/history_guided_bug_discovery/  domain, pipeline, adapters, evaluator, reporting, CLI
configs/                            versioned run configuration
data/                               case manifests, raw/structured history, leakage boundaries
artifacts/                          preserved runs, execution logs, and replay bundles
generated_tests/                    preserved generated test source
results/                            authoritative CSVs and evidence reports
scripts/                            preparation, evaluation, replay, and verification tools
tests/                              unit, contract, integration, and evidence checks
docs/                               architecture, reproducibility, and engineering reports
```

## Installation

From the repository root:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

The package requires Python 3.11 or newer. Live generation reads `DEEPSEEK_API_KEY` from the environment and never prints or stores it. Offline verification does not require the key.

## Offline verification

These commands read preserved evidence only and work from the repository root:

```bash
python -m compileall scripts tests
python -m pytest -q
python scripts/verify_core_results.py
python scripts/verify_experiment4_artifacts.py
replay --config configs/experiment4.json --artifacts artifacts/experiment4/iteration3 --arm C2
replay --config configs/experiment4.json --artifacts artifacts/experiment4/iteration3 --arm C1_BUDGETED
```

The core verifier derives both A/B/C tables from the authoritative Experiment 2 CSVs. The Experiment 4 verifier checks frozen CSV hashes, evidence-bundle hashes, replay metrics, and report consistency. Neither verifier makes an LLM call.

If the preserved target checkouts and their Python 3.9 environments are available, replay the harness separation check with:

```bash
python scripts/verify_harness.py
```

It must report `buggy=1` and `fixed=0`. The external harness is optional for offline evidence replay.

## Reproducing recorded experiments

The repository records the Experiment 2 clean replication in `results/experiment2_replication2.csv` and the cumulative re-evaluation in `results/experiment2_re_evaluated.csv`. Run `python scripts/verify_core_results.py` to reproduce their aggregate checks without starting a new generation run. The Experiment 4 evidence can be replayed with the commands above; its detailed accounting and failure analysis are linked from [`docs/engineering-results.md`](docs/engineering-results.md) and [`docs/experiment4-report.md`](docs/experiment4-report.md).

## Limitations and scope

- One selected `PySnooper:1` target and one retrospectively selected transfer-feasibility case.
- Small attempt counts and no statistical significance claim.
- History retrieval quality is not evaluated; history selection was retrospective.
- Clean replication mechanism matches did not produce F2P tests.
- The current POC does not establish broad cross-project generalization.
- A valid plan or mechanism match is not a semantic proof; executable differential evaluation remains necessary.

## Detailed reports

- [`docs/engineering-results.md`](docs/engineering-results.md) — evidence-backed engineering journey.
- [`FOLLOWUP_REPORT.md`](FOLLOWUP_REPORT.md) — concise outcome report.
- [`docs/architecture.md`](docs/architecture.md) — proposed stages and implementation status.
- [`docs/experiment4-report.md`](docs/experiment4-report.md) — downstream Trigger Plan evidence.
- [`docs/reproducibility.md`](docs/reproducibility.md) — offline replay and provenance details.
