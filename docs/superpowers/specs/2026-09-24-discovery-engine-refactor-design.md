# Experiment 4 Discovery Engine Refactor

## Context

Experiment 4 currently mixes research orchestration, DeepSeek transport, prompt
construction, target checkout paths, subprocess execution, evaluator semantics,
and CSV writing in script-level dictionaries. The raw Experiment 4 artifacts are
the empirical source of truth and must remain byte-for-byte unchanged.

The refactor keeps the research hypothesis and evaluator semantics intact while
making the implementation reusable for another target, provider, or run.

## Design

The new `history_guided_bug_discovery` package is organized around four layers:

1. `domain` contains frozen, versioned dataclasses and enums. Domain models
   serialize deterministically and separate generation-visible provenance from
   evaluator-only truth.
2. `ports` defines protocols for model generation, target preparation, test
   execution, evaluation, and artifact persistence. The application layer only
   consumes these protocols.
3. `adapters` implements DeepSeek, BugsInPy, subprocess execution, the shared
   benchmark evaluator, and an append-only JSONL artifact store.
4. `application` coordinates typed stage transitions and prompt strategies;
   `reporting` aggregates authoritative rows into CSV, JSON, and Markdown.

The pipeline records the requested stages as immutable `RunEvent` entries. A
run manifest records the source commit, deterministic config hash, generation
visible input manifest, prompt hashes, model metadata, and evaluator version.
The live pipeline can use direct, strict-planner, or budget-matched direct arms;
the replay pipeline consumes preserved Experiment 4 rows and never constructs
an LLM provider.

## Evaluation boundary

`BenchmarkEvaluator` may compare buggy and fixed revisions for empirical
validation and owns the preserved classification rules. `FindingValidator` is
the product-side interface and does not require a fixed revision. Generation
services receive only the target context, structured history, frozen hypothesis,
and validated plan. Fixed checkouts, issue reports, patches, regression tests,
and evaluator verdicts are adapter/evaluator inputs only.

## Compatibility and migration

The existing `scripts/run_experiment4.py` and
`scripts/evaluate_experiment4.py` become argument-preserving wrappers. The
existing plan-contract module re-exports the new validator so historical tests
and imports continue to work. Raw result CSVs, generated tests, execution logs,
and frozen hypotheses are not rewritten.

## Verification

Unit and contract tests cover serialization, configuration validation, planner
validation, preflight, execution, evaluator semantics, ledger behavior, and
report consistency. A golden replay reads the preserved iteration-3 C2 and
budgeted-C1 result artifacts and asserts the frozen baseline counts without an
API key or model call.
