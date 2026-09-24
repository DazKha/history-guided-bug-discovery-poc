# Experiment 4 Engineering Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden the preserved Experiment 4 workflow without changing its empirical evidence or evaluator semantics.

**Architecture:** Keep the existing `src/` domain/application/adapter layout. Add a focused evidence-bundle verifier and provider registry, make the pipeline ledger-driven for resume, harden subprocess file lifecycle, and expose the system through packaging and CI.

**Tech Stack:** Python 3.11+, pytest, requests, setuptools-compatible `pyproject.toml`, GitHub Actions.

## Global Constraints

- Preserve the two authoritative CSV bytes and SHA-256 hashes.
- Replay is deterministic evidence validation, never target re-execution.
- Replay/report/evaluation-only commands never construct an LLM provider.
- Never make a live LLM call during cleanup or verification.
- Do not change benchmark evaluator semantics.
- Do not use external BugsInPy checkouts for offline verification.

### Task 1: Evidence bundle and replay validation

**Files:**
- Create: `src/history_guided_bug_discovery/application/evidence_bundle.py`
- Modify: `src/history_guided_bug_discovery/application/replay_pipeline.py`
- Create: `scripts/prepare_experiment4_evidence_bundle.py`
- Create: `scripts/verify_experiment4_artifacts.py`
- Test: `tests/integration/test_golden_replay.py`, `tests/unit/test_evidence_bundle.py`

- [ ] Write failing tests for manifest discovery, hash validation, aggregate mismatch, and offline replay.
- [ ] Run the focused tests and observe failures caused by the absent bundle contract.
- [ ] Implement immutable per-arm manifests and co-located row snapshots; make replay read only those files.
- [ ] Generate the checked-in snapshots from the authoritative CSVs without modifying those CSVs.
- [ ] Run focused replay and verification tests.

### Task 2: Packaging, configuration, and provider registry

**Files:**
- Create: `pyproject.toml`
- Create: `src/history_guided_bug_discovery/adapters/providers.py`
- Modify: `src/history_guided_bug_discovery/config/loader.py`, `src/history_guided_bug_discovery/config/models.py`, `src/history_guided_bug_discovery/cli/run.py`, compatibility scripts, `README.md`
- Test: `tests/unit/test_domain_config.py`, `tests/unit/test_cli_configuration.py`

- [ ] Write failing tests for unsupported providers and external-CWD config paths.
- [ ] Run the focused tests and observe failures.
- [ ] Implement package metadata, console scripts, root-based target paths, and explicit provider selection.
- [ ] Install editable with dev extras and run focused tests.

### Task 3: Stage-aware resume

**Files:**
- Modify: `src/history_guided_bug_discovery/application/discovery_pipeline.py`, `src/history_guided_bug_discovery/adapters/json_artifact_store.py`, `src/history_guided_bug_discovery/ports/artifact_store.py`
- Test: `tests/unit/test_resume_pipeline.py`

- [ ] Write deterministic crash/resume tests for generation, buggy execution, fixed execution, and evaluation boundaries.
- [ ] Run them red against the current whole-candidate skip behavior.
- [ ] Implement ledger indexes, artifact round-tripping/hash checks, stage continuation, and ledger-derived summaries.
- [ ] Run the resume tests and the full suite.

### Task 4: Executor hardening and public-tree cleanup

**Files:**
- Modify: `src/history_guided_bug_discovery/adapters/subprocess_executor.py`
- Test: `tests/unit/test_pipeline.py`, `tests/unit/test_subprocess_executor.py`
- Delete: tracked excluded-experiment files under `scripts/`, `data/`, `artifacts/`, `generated_tests/`, and `results/`

- [ ] Write failing tests for collisions, unsafe identifiers, timeout/exception cleanup, missing checkout/interpreter, and normal classifications.
- [ ] Implement safe unique injection and clear preflight errors.
- [ ] Remove only explicitly excluded tracked material and verify the public-tree searches are empty.

### Task 5: CI and documentation

**Files:**
- Create: `.github/workflows/experiment4.yml`
- Modify: `docs/architecture.md`, `docs/reproducibility.md`, `docs/artifact-schema.md`, `docs/experiment4-report.md`, `README.md`
- Test: `tests/test_reproducibility_docs.py`

- [ ] Add exact clean-install and offline verification commands.
- [ ] Add the Python 3.11/3.12 workflow with no secret or checkout dependency.
- [ ] Run compilation, the complete suite, clean-venv acceptance, frozen hash checks, and artifact verification.
- [ ] Review the diff, commit, push normally, and inspect CI if available.
