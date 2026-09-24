# History-Guided Bug Discovery PoC

An engineering proof of concept for one vertical slice of a history-guided bug discovery pipeline: historical bug evidence is transformed into structured failure knowledge, transferred into target-specific hypotheses, turned into executable tests, and evaluated by buggy/fixed differential execution.

## TL;DR

The implemented question is deliberately narrow:

> After relevant historical bugs have already been retrieved, does converting their raw evidence into structured, mechanism-oriented knowledge help an agent propose better target-specific bug hypotheses than using no history or raw history alone?

The clean comparison holds the target, model/configuration, generation budget, runtime controls, and evaluation rubric constant across three input configurations:

| Input configuration | Mechanism-aligned hypotheses | Attempts | Verified F2P |
| --- | ---: | ---: | ---: |
| Target context only | 0 | 10 | 0 |
| Target + raw historical evidence | 1 | 10 | 0 |
| Target + structured historical knowledge | 6 | 10 | 0 |

The evidence supports a narrow engineering conclusion: on one selected BugsInPy target under this controlled pipeline comparison, the structured-history module increased mechanism-aligned hypotheses from 0/10 for target-only and 1/10 for raw history to 6/10. It supports value at the mechanism-targeting stage, not stable end-to-end executable bug discovery. The clean replication produced zero verified F2P for all three configurations.

## Engineering PoC scope

This repository implements and preserves a bounded vertical slice with defined inputs and outputs, controlled baselines, an evaluator and acceptance criteria, immutable evidence artifacts, reproducible verification commands, and an identified downstream bottleneck.

```mermaid
flowchart LR
    H[Historical bug evidence] --> S[Structured historical knowledge]
    S --> T[Target-specific mechanism hypothesis]
    T --> G[Executable test generation]
    G --> D[Buggy/fixed differential evaluation]
    D --> A[Preserved artifacts and reports]
```

The current implementation covers:

- fixed target context and selected historical inputs;
- raw and structured historical evidence records;
- three controlled hypothesis-generation baselines;
- frozen hypothesis and generated-test artifacts;
- buggy/fixed execution and classification;
- execution logs, CSV results, replay bundles, and deterministic verifiers.

Autonomous retrieval, learned ranking, and memory learning are outside this PoC. Historical selection was retrospective to test transfer feasibility.

## Implemented vertical slice

| Stage | Input | Output | Status |
| --- | --- | --- | --- |
| Historical evidence | BugsInPy historical cases | Raw records with commits, diffs, and regression evidence | Implemented |
| Structured history | Raw historical records | Mechanism-oriented records with applicability evidence | Implemented as prepared data |
| Target understanding | Held-out buggy checkout and visible runtime facts | Bounded target context | Implemented for the selected target |
| Hypothesis generation | Target context plus condition-specific history | One frozen candidate hypothesis per attempt | Implemented |
| Test generation | Frozen hypothesis | Candidate test source and execution metadata | Implemented; downstream bottleneck remains |
| Differential evaluation | Unchanged candidate test, buggy revision, fixed revision | F2P/F2F/P2P/P2F and mechanical classifications | Implemented |

The central module is the raw-to-structured history transformation. It makes transferable failure knowledge explicit so the agent can decide whether a historical mechanism applies to the target before proposing a trigger. It does not claim to implement a general historical-memory or autonomous-retrieval system.

## Data source and selected cases

The data source is [BugsInPy](https://github.com/soarsmu/BugsInPy), using the benchmark revision recorded in [`data/case_manifest.json`](data/case_manifest.json).

- Held-out target: `PySnooper:1`.
- Historical inputs: `cookiecutter:1` and `PySnooper:3`.
- The historical bugs are evidence inputs, not additional target bugs.
- The target and historical inputs were fixed for the comparison.
- Historical selection was retrospective and tests transfer feasibility; autonomous retrieval quality is not evaluated.

BugsInPy evidence includes buggy and fixed revisions, commit information, fix diffs, and regression evidence. In the committed historical records, standalone issue text is not available; the fixed commit subject is retained as the available report surrogate. The raw records also preserve source references, fix diffs, and regression tests in [`data/experiment2_historical_raw.json`](data/experiment2_historical_raw.json).

The target's ordinary runtime is Python 3.9.18 with `LC_ALL=C`, `PYTHONUTF8=0`, and `PYTHONCOERCECLOCALE=0`. The evaluator-only target truth is preserved in [`data/evaluator_truth/experiment2_PySnooper-1.json`](data/evaluator_truth/experiment2_PySnooper-1.json).

## Raw history versus structured history

Raw history preserves the evidence as supplied to the comparison: historical identifiers, project, report surrogate, commit subject, buggy/fixed commit IDs, fix diff, regression test, and source references.

Structured history is the implemented transformation used by the structured-history condition. The committed records in [`data/experiment2_historical_structured.json`](data/experiment2_historical_structured.json) make the following fields explicit:

- `Context`
- `Preconditions`
- `Trigger`
- `Expected Invariant`
- `Observed Failure`
- `Failure Mechanism`
- `Oracle`
- `Oracle Provenance`
- `Test Strategy`
- `Evidence References`
- `Confidence`, including mechanism, trigger, invariant, and transfer-to-target confidence

This representation separates what must be true before the bug, what action exposes it, what invariant should hold, what failed, what mechanism is suspected, and why the oracle is supported. It is intended to make failure knowledge easier to transfer; it is not a learned ranking or retrieval component.

## Controlled input configurations

The comparison uses the same selected target, model/configuration, attempt count, generation budget, repair budget, runtime controls, and evaluation rubric in every condition. The leakage manifest records a maximum of one repair per run; the clean replication assembles two five-attempt halves into 10 attempts per condition. Only the historical input representation changes:

| Condition | Recorded name | Agent-visible history |
| --- | --- | --- |
| A | `TARGET_ONLY` | None |
| B | `NAIVE_RAW_HISTORY` | The selected raw historical evidence |
| C | `STRUCTURED_APPLICABILITY_AWARE` | The same historical cases represented as structured knowledge with applicability decisions |

Raw-history and structured-history conditions therefore use the same underlying historical cases. The fairness and leakage boundaries are recorded in [`data/target_leakage_manifest.json`](data/target_leakage_manifest.json).

## What one attempt means

One attempt is one independent hypothesis-generation run. Each run produces one candidate hypothesis. There are 10 runs per input configuration, for 30 runs in the clean comparison.

These are:

- not 30 targets;
- not 30 discovered bugs;
- not necessarily 30 executable tests.

The 10 attempts per condition are composed of the preserved `replication2b` and `replication2c` batches: two five-attempt halves for each condition. Some hypotheses produce generated tests; some tests are mechanical failures or do not distinguish the revisions.

## Reference mechanism and mechanism alignment

The evaluator-only reference mechanism for `PySnooper:1` is:

- trace/source data contains non-ASCII text;
- the process runs under a controlled non-UTF-8/C locale;
- buggy file/source I/O relies on implicit or locale-dependent text encoding;
- the fixed revision uses explicit UTF-8 handling.

In plain engineering terms, the target should trace a function containing non-ASCII data and preserve valid UTF-8 trace/source output even when the runtime default encoding is not UTF-8. The evaluator truth describes the trigger, expected invariant, actual failure, failure mechanism, and oracle. The reference mechanism is used only for evaluator-side labeling; it is not exposed during generation.

A mechanism-aligned hypothesis identifies all relevant parts of the causal pattern:

1. the target component or behavior;
2. the trigger or precondition;
3. the causal failure pattern.

Merely mentioning a keyword such as “Unicode” is not sufficient. Mechanism alignment is an upstream hypothesis-quality signal. Verified F2P is downstream executable differential evidence.

> **Interpretation warning:** 6/10 mechanism-aligned hypotheses does not mean six bugs were discovered or six executable regression tests succeeded.

## Leakage controls

Generation cannot access the following target-specific information:

- target issue/report;
- fixed target implementation;
- target fix diff;
- hidden target regression test;
- changed-file metadata;
- reference mechanism;
- evaluator outcome.

The fixed revision is evaluator-only. The complete agent-visible/evaluator-only boundary is documented in [`data/target_leakage_manifest.json`](data/target_leakage_manifest.json), including the target report, patch, hidden test, fixed checkout, and truth file that remain outside generation.

## Differential execution and acceptance labels

The same generated test is run unchanged against the buggy and fixed revisions. The fixed revision is used only by the evaluator. The strongest verification signal in this repository is:

```text
T(B) = FAIL
T(F) = PASS
```

| Buggy revision | Fixed revision | Label | Meaning |
| --- | --- | --- | --- |
| FAIL | PASS | F2P | Desired differential trigger |
| FAIL | FAIL | F2F | Usually invalid setup, overly broad assertion, or unrelated failure |
| PASS | PASS | P2P | Test does not distinguish the revisions |
| PASS | FAIL | P2F | Inverted or anomalous result |

Syntax, import, collection, dependency, timeout, and unrelated environment failures are mechanical failures. They are not semantic F2P evidence. Verified F2P is the strongest downstream signal used in the repository.

## Main clean result

The authoritative clean replication is [`results/experiment2_replication2.csv`](results/experiment2_replication2.csv), checked by [`scripts/verify_core_results.py`](scripts/verify_core_results.py):

| Input configuration | Mechanism-aligned hypotheses | Attempts | Verified F2P |
| --- | ---: | ---: | ---: |
| Target context only | 0 | 10 | 0 |
| Target + raw historical evidence | 1 | 10 | 0 |
| Target + structured historical knowledge | 6 | 10 | 0 |

This is the main result: structured history improved mechanism targeting in the selected case, but the clean replication did not produce a verified buggy/fixed differential trigger in any condition.

## Engineering interpretation

The pipeline separates two engineering problems:

1. identify a target-specific failure mechanism;
2. construct a valid precondition, state/action sequence, observable, and assertion that exposes it.

The structured-history module improved the first stage under this protocol. The remaining instability was in translating a plausible mechanism into an executable trigger and oracle. This is why the README reports mechanism alignment and verified F2P separately.

## Supporting cumulative evidence

The cumulative record in [`results/experiment2_re_evaluated.csv`](results/experiment2_re_evaluated.csv) combines 25 attempts per condition across the preserved exploratory and replication batches:

| Input configuration | Mechanism-aligned hypotheses | Attempts | Verified F2P |
| --- | ---: | ---: | ---: |
| Target context only | 0 | 25 | 0 |
| Target + raw historical evidence | 2 | 25 | 0 |
| Target + structured historical knowledge | 15 | 25 | 2 |

The two cumulative F2P results occurred in exploratory structured-history runs and did not reproduce in the clean replication. They are feasibility evidence, not proof of stable end-to-end improvement.

## Remaining bottleneck

The downstream bottleneck is executable trigger construction. A hypothesis can identify the right encoding, state, or sequencing mechanism and still produce a weak trigger, a wrong-shaped assertion, an invalid test, or a failure caused by setup rather than the target defect. The preserved generated tests and execution logs make these failure modes inspectable.

## Engineering follow-up: Trigger Plan

The Trigger Plan is a downstream engineering improvement to executable-test generation, not the main project contribution. Before code generation, it makes these items explicit:

- preconditions;
- initial state;
- action sequence;
- expected invariant;
- observable and measurement point;
- assertion strategy;
- setup requirements;
- timeout.

In the budget-matched Experiment 4 evidence, plan validity improved from 2/5 to 5/5 hypotheses. Planner hypothesis-level F2P coverage was 4/5 versus 3/5 for direct generation. Direct generation remained more efficient per generated candidate: 6/15 F2P versus 5/15 for the planner. The result is mixed: Trigger Plans improved reliability and coverage, not normalized per-test efficiency. Details and replay instructions are in [`docs/experiment4-report.md`](docs/experiment4-report.md).

## Important metrics

| Metric | Definition |
| --- | --- |
| Attempts | Independent hypothesis-generation runs; one candidate hypothesis per run |
| Mechanism matches | Attempts labeled as identifying the evaluator's full reference mechanism, not just a keyword |
| Mechanism-match rate | Mechanism matches divided by attempts |
| Valid-plan rate | Valid Trigger Plans divided by planner hypotheses/plan attempts under the recorded planner contract |
| Generated tests | Preserved candidate test artifacts produced after hypothesis generation |
| Executable-test rate | Generated tests that pass preflight/collection and reach the intended evaluator execution, divided by generated tests |
| Hypothesis-level F2P | Hypotheses with at least one verified F2P divided by the frozen-hypothesis denominator for that run |
| F2P per generated test | Verified F2P outcomes divided by the stated generated-candidate denominator; the Trigger Plan comparison uses 15 candidate slots per arm |
| F2P per executable test | Verified F2P outcomes divided by executable generated tests |
| Executions per F2P | Buggy/fixed test executions divided by verified F2P outcomes |
| LLM calls per F2P | Recorded model calls divided by verified F2P outcomes |
| Mechanical failure | Syntax, import, collection, dependency, timeout, or unrelated environment failure; not semantic F2P evidence |

The repository's recorded reports preserve the denominator used for each metric. Metrics with zero F2P have no finite per-F2P efficiency value.

## Current implementation status

Implemented:

- BugsInPy case manifest and selected target adapter;
- leakage-separated target context and evaluator-only truth;
- raw and structured historical evidence records;
- controlled A/B/C input configurations;
- hypothesis freezing and generated-test artifact preservation;
- buggy/fixed differential execution and classification;
- execution logs, result CSVs, replay bundles, and deterministic verification;
- downstream Trigger Plan validation and bounded repair.

Partially implemented or outside scope:

- historical selection is retrospective rather than autonomous retrieval;
- structured records are prepared data, not learned memory updates;
- target understanding is a bounded slice for one selected target;
- end-to-end F2P reliability remains the downstream bottleneck.

## Repository layout

```text
src/history_guided_bug_discovery/  domain, pipeline, adapters, evaluator, reporting, CLI
configs/                            versioned run configuration
data/                               case, history, evaluator-truth, and leakage manifests
artifacts/                          preserved runs, replay bundles, and execution logs
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

The package requires Python 3.11 or newer. Live generation reads `DEEPSEEK_API_KEY` from the environment and never prints, logs, or stores it. Offline verification does not require the key.

## Offline verification

From the repository root, the evidence-only verification sequence is:

```bash
python -m compileall scripts tests
python -m pytest -q
python scripts/verify_core_results.py
python scripts/verify_experiment4_artifacts.py
replay --config configs/experiment4.json --artifacts artifacts/experiment4/iteration3 --arm C2
replay --config configs/experiment4.json --artifacts artifacts/experiment4/iteration3 --arm C1_BUDGETED
```

The core verifier reads the authoritative Experiment 2 CSVs and derives the clean and cumulative tables; it does not start an LLM call. The Experiment 4 verifier checks frozen CSV hashes, evidence-bundle hashes, replay metrics, and report consistency. The integration golden-replay test can also be run directly:

```bash
python -m pytest -q tests/integration/test_golden_replay.py
```

## Optional external harness verification

If the preserved PySnooper buggy/fixed checkouts and their Python 3.9 environments are available, run:

```bash
python scripts/verify_harness.py
```

The expected machine-readable result is `buggy=1` and `fixed=0`. This check depends on external target checkouts; if they are absent, report it as skipped. Offline evidence verification remains valid without them.

## Reproducing recorded experiments

The clean Experiment 2 replication is preserved in `results/experiment2_replication2.csv`; the cumulative record is preserved in `results/experiment2_re_evaluated.csv`. The commands above reproduce their aggregate checks without starting a new generation run. Experiment 4 is replayable from its preserved artifacts and configuration; its detailed accounting is in [`docs/experiment4-report.md`](docs/experiment4-report.md).

## Limitations and claim boundary

This repository does not prove the full history-guided architecture. The defensible claim is limited to one selected BugsInPy target under a controlled pipeline comparison:

- there is only one selected target, `PySnooper:1`;
- attempt counts are small;
- no statistical-significance or broad-generalization claim should be made;
- history retrieval quality was not evaluated;
- historical selection was retrospective;
- the clean replication produced zero verified F2P for all three configurations;
- the cumulative two F2P results are exploratory feasibility evidence and did not reproduce cleanly;
- mechanism alignment is not equivalent to executable bug discovery.

The evidence supports structured history as a mechanism-targeting intervention. It does not yet establish stable end-to-end executable bug discovery.

## Detailed documentation and artifacts

- [`docs/engineering-results.md`](docs/engineering-results.md) — evidence-backed engineering results and interpretation.
- [`docs/architecture.md`](docs/architecture.md) — proposed stages and implementation status.
- [`docs/reproducibility.md`](docs/reproducibility.md) — offline replay, provenance, and external harness details.
- [`docs/experiment4-report.md`](docs/experiment4-report.md) — downstream Trigger Plan evidence.
- [`FOLLOWUP_REPORT.md`](FOLLOWUP_REPORT.md) — concise outcome report.
- [`research_log.md`](research_log.md) — recorded data sources and research notes.
- [`data/case_manifest.json`](data/case_manifest.json) — BugsInPy source, target, runtime, and case selection.
- [`data/target_leakage_manifest.json`](data/target_leakage_manifest.json) — agent-visible and evaluator-only boundaries.
- [`data/evaluator_truth/experiment2_PySnooper-1.json`](data/evaluator_truth/experiment2_PySnooper-1.json) — evaluator-only reference mechanism and oracle.
- [`data/historical_raw.json`](data/historical_raw.json) and [`data/historical_structured.json`](data/historical_structured.json) — preserved historical evidence outputs.
- [`results/experiment2_replication2.csv`](results/experiment2_replication2.csv) — clean replication rows.
- [`results/experiment2_re_evaluated.csv`](results/experiment2_re_evaluated.csv) — cumulative supporting rows.
- [`results/results.csv`](results/results.csv), [`results/summary.csv`](results/summary.csv), and [`results/failure_analysis.md`](results/failure_analysis.md) — preserved result summaries and failure analysis.
- [`generated_tests/`](generated_tests/) and [`artifacts/execution_logs/`](artifacts/execution_logs/) — generated-test source and execution logs.
