# Reframe History-Guided Results Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reposition the repository around the structured-history mechanism-targeting result, add deterministic verification for the clean and cumulative Experiment 2 evidence, and keep Trigger Plans as a secondary engineering follow-up.

**Architecture:** Preserve all recorded evidence, evaluator semantics, frozen hypotheses, generated tests, and Experiment 4 implementation. Add a read-only CSV verifier that derives core metrics from the authoritative Experiment 2 files, then align the public documentation and CI workflow to that verifier and the existing Experiment 4 verifier.

**Tech Stack:** Python 3.11+, csv, pytest, Markdown, GitHub Actions.

## Global Constraints

- Do not run new LLM experiments or modify recorded outcomes.
- Do not modify evaluator semantics, historical CSV rows, frozen hypotheses, generation algorithms, or generated tests.
- Do not expose retired later-experiment artifacts or references.
- Preserve and verify the existing Experiment 4 implementation and evidence hashes.
- Do not make claims about broad generalization or statistical significance.
- Read `DEEPSEEK_API_KEY` only from the environment; never print or persist it.

---

### Task 1: Add deterministic core-evidence verification

**Files:**
- Create: `scripts/verify_core_results.py`
- Create: `tests/test_verify_core_results.py`

**Interfaces:**
- `summarize_csv(path: Path, spec: DatasetSpec) -> dict[str, Metrics]` reads and validates one authoritative CSV.
- `verify_csv(path: Path, spec: DatasetSpec) -> dict[str, Metrics]` derives counts and raises a useful `ValueError` on disagreement.
- `verify_recorded_results(root: Path = ROOT) -> dict[str, dict[str, Metrics]]` verifies the clean and cumulative sources.

- [ ] Write tests for successful clean/cumulative verification using the checked-in CSVs.
- [ ] Write tests for incorrect counts, missing conditions, and malformed or missing required fields.
- [ ] Run `pytest -q tests/test_verify_core_results.py` and observe failure because the verifier module is not yet present.
- [ ] Implement strict schema validation, source-batch validation, boolean parsing, per-condition aggregation, and expected-value comparison.
- [ ] Run the focused tests and then the verifier command.

### Task 2: Reframe repository documentation

**Files:**
- Modify: `README.md`
- Modify: `FOLLOWUP_REPORT.md`
- Create: `docs/engineering-results.md`
- Modify: `docs/architecture.md`
- Modify: `docs/reproducibility.md`

- [ ] Put the controlled A/B/C comparison and its clean zero-F2P result before Experiment 4 discussion.
- [ ] Explain structured history as the main intervention and Trigger Plans as downstream executable-test engineering.
- [ ] State the selected transfer-feasibility target, retrospective history selection, and scope limitations.
- [ ] Align architecture stages and label implemented, partial, and proposed components.
- [ ] Link detailed evidence and the new offline verifier.

### Task 3: Generalize CI and verify the repository

**Files:**
- Modify: `.github/workflows/experiment4.yml`

- [ ] Rename the workflow display name to `Offline evidence verification`.
- [ ] Add compilation, full tests, core evidence verification, Experiment 4 verification/replay, and existing harness/leakage checks without removing current coverage.
- [ ] Run all local checks from the repository root, including the supported buggy/fixed replay.
- [ ] Confirm Experiment 4 evidence hashes are unchanged and no retired later-experiment text is present.
- [ ] Review the complete diff, commit, push, and inspect the resulting GitHub Actions run.
