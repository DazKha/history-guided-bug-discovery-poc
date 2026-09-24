# Experiment 4 Discovery Engine Refactor Implementation Plan

> **For agentic workers:** Execute this plan task-by-task in the current repository. Keep raw Experiment 4 artifacts unchanged and run the listed tests after each task.

**Goal:** Refactor Experiment 4 into a typed, configuration-driven discovery engine with reusable adapters, replay, reporting, compatibility wrappers, and a verified golden baseline.

**Architecture:** Immutable domain dataclasses flow through application services via protocol ports. Adapters isolate DeepSeek, BugsInPy checkouts, subprocess execution, benchmark-only evaluation, and JSONL persistence. Reporting consumes authoritative machine-readable rows and produces consistent CSV/JSON/Markdown outputs.

**Tech Stack:** Python standard library dataclasses, enums, pathlib, protocols, JSON/JSONL, csv, subprocess, ast, hashlib; existing `requests` and `pytest` only where already used.

## Global Constraints

- Preserve the frozen Experiment 4 empirical results and evaluator semantics.
- Never call the LLM during tests, replay, report generation, or verification.
- Do not modify raw Experiment 4 CSV rows, generated tests, execution logs, or frozen hypotheses.
- Keep generation blind to fixed revisions, patches, issue reports, hidden tests, and evaluator truth.
- Preserve backward-compatible Experiment 4 script entry points.

### Task 1: Typed domain and configuration

Create `src/history_guided_bug_discovery/domain/` models/enums/errors and
`config/` loader/models. Add unit tests for deterministic serialization,
immutability, enum round-trips, config hashes, unknown fields, relative paths,
and invalid budgets/timeouts. Add `configs/experiment4.json` pointing to the
existing data and target manifest.

### Task 2: Ports and adapters

Add protocol ports and adapters for DeepSeek, BugsInPy target preparation,
subprocess execution, benchmark evaluation, JSONL artifacts, and deterministic
preflight. Port the current plan validator and evaluator classification rules
without changing their meanings. Add contract tests using temporary fixture
repositories and fake providers.

### Task 3: Application pipeline and prompts

Add explicit prompt strategy builders (`direct_test_v1`,
`strict_trigger_plan_v1`, `plan_to_test_compact_v1`), hypothesis/planning/test
generation services, and a staged discovery pipeline. Each stage emits typed
events and supports direct, strict-planner, budget-matched direct, and resume
semantics. Add service tests with fake providers and stores.

### Task 4: Replay and reporting

Implement offline replay over preserved iteration-3 raw CSVs and an aggregate
model with consistency checks. Produce JSON, CSV, and Markdown summaries from
rows rather than literal metric constants. Add golden replay and cross-format
consistency tests for C2 and budgeted C1.

### Task 5: CLI and compatibility wrappers

Add `cli.run`, `cli.evaluate`, `cli.replay`, and `cli.report`. Convert the two
Experiment 4 scripts to thin wrappers and retain the plan-contract import
surface. Verify no live provider is constructed by replay/report commands.

### Task 6: Documentation and cleanup

Rewrite the README for the engineering system and add architecture,
artifact-schema, reproducibility, and Experiment 4 report documents. Run the
full quality gates, inspect staged diffs, and leave unrelated historical
research files untouched.
