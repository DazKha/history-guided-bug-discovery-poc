# Experiment 3 Trigger Construction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add and execute a leakage-safe Experiment 3 that isolates generic trigger diversification after a frozen structured-history hypothesis.

**Architecture:** Add new Experiment 3 modules beside the preserved Experiment 2 runner. A generation runner creates frozen hypotheses, a trigger planner creates four structured candidates, a test generator instantiates one pytest per candidate, and a new evaluator adapter runs unchanged tests through the existing evaluator semantics without changing its classification logic. Report writers derive all metrics from immutable JSON/CSV artifacts.

**Tech Stack:** Python 3.13, pytest, existing DeepSeek client, JSON/CSV/Markdown, subprocess execution against the existing BugsInPy PySnooper harness.

## Global Constraints

- Preserve all Experiment 2 code and artifacts.
- Never expose fixed source, diffs, issue text, regression tests, benchmark truth, or evaluator labels to generation.
- Freeze the hypothesis before trigger planning and do not regenerate it per trigger.
- Use exactly four trigger candidates per hypothesis, subject to schema/relevance filtering.
- Keep current evaluator semantics and oracle policy unchanged.
- Never print or persist `DEEPSEEK_API_KEY`.
- Run real commands and report execution evidence, including negative results.

---

### Task 1: Commit the approved design and establish test seams

**Files:**
- Create: `docs/superpowers/specs/2026-09-23-trigger-construction-experiment3-design.md`
- Create: `docs/superpowers/plans/2026-09-23-trigger-construction-experiment3-plan.md`
- Create: `tests/test_experiment3_contracts.py`

**Interfaces:**
- Tests import `scripts.experiment3_trigger_planner`, `scripts.experiment3_metrics`, and `scripts.experiment3_runner`.

- [ ] **Step 1: Write failing contract tests**

  Test trigger schema validation rejects missing fields, accepts the five allowed trigger types, keeps hypotheses immutable across planning, and computes one row per trigger/test pair.

- [ ] **Step 2: Run the contract tests and verify the expected import failures**

  Run `pytest -q tests/test_experiment3_contracts.py`; expected result is failure because the Experiment 3 modules do not yet exist.

- [ ] **Step 3: Add only the design and plan documents**

  Confirm the documents state the leakage boundary, frozen variables, C1/C2 arms, N=4, budget normalization, and unchanged evaluator semantics.

- [ ] **Step 4: Commit the design checkpoint**

  Run `git add docs/superpowers/specs/2026-09-23-trigger-construction-experiment3-design.md docs/superpowers/plans/2026-09-23-trigger-construction-experiment3-plan.md tests/test_experiment3_contracts.py` and commit with `git commit -m "docs: design experiment3 trigger construction study"`.

### Task 2: Implement generic trigger planning and frozen-hypothesis contracts

**Files:**
- Create: `scripts/experiment3_trigger_planner.py`
- Create: `scripts/experiment3_runner.py`
- Modify: `tests/test_experiment3_contracts.py`

**Interfaces:**
- `validate_trigger(candidate: dict) -> dict` validates and normalizes one candidate.
- `deduplicate_triggers(candidates: list[dict], limit: int = 4) -> list[dict]` keeps meaningfully distinct candidates in stable order.
- `build_trigger_prompt(hypothesis: dict, target_context: str, history: list[dict], count: int = 4) -> str` builds a no-leak prompt.
- `freeze_hypothesis(record: dict) -> dict` returns a deep copy with `hypothesis_frozen=True` and immutable text fields.

- [ ] **Step 1: Add tests for validation, diversity, and leakage controls**

  Assert that invalid trigger types fail, duplicate semantic dimensions collapse, exactly four distinct candidates are requested, and forbidden strings such as fixed checkout, diff, regression test, or evaluator truth are absent from the prompt builder inputs/visible-file manifest.

- [ ] **Step 2: Run the focused tests red**

  Run `pytest -q tests/test_experiment3_contracts.py -k 'trigger or freeze'`; expected failures identify missing functions.

- [ ] **Step 3: Implement the smallest pure planner layer**

  Implement schema validation, normalized diversity keys based on trigger type plus setup/action/environment, and a deterministic prompt builder. Do not add hidden-target heuristics or execution feedback here.

- [ ] **Step 4: Run focused tests green**

  Run the same pytest command and inspect that no API key or evaluator-only path appears in generated prompt text.

### Task 3: Implement generation for Experiment 3A and conditional 3B

**Files:**
- Create: `scripts/run_experiment3.py`
- Create: `prompts/experiment3_C1_direct.md`
- Create: `prompts/experiment3_C2_trigger_planner.md`
- Create: `data/experiment3_hypotheses.json`
- Create: `data/experiment3_conditional_hypotheses.json`
- Create: `artifacts/experiment3_llm/`
- Create: `generated_tests/experiment3/`
- Modify: `tests/test_experiment3_contracts.py`

**Interfaces:**
- `run_experiment3.py --mode natural|conditional --arm C1|C2 --attempts 5` writes immutable hypothesis, trigger, test, usage, and visible-file manifest records.
- C1 stores one direct test per frozen hypothesis; C2 stores one test-generation call per retained trigger.

- [ ] **Step 1: Add runner contract tests with a fake client**

  Assert C2 carries the exact same serialized hypothesis into all trigger-generation/test-generation records and that C1/C2 use the same context/history files.

- [ ] **Step 2: Run the new runner tests red**

  Run `pytest -q tests/test_experiment3_contracts.py -k runner`; expected failure is missing runner implementation.

- [ ] **Step 3: Implement natural and conditional runners**

  Use the existing `DeepSeekClient` and model settings. Natural mode creates hypotheses with the existing structured-history schema; conditional mode reads only stored mechanism-matched hypotheses exported by evaluator-facing preparation, but generation receives no match labels. Record all prompt/completion usage and never store the secret.

- [ ] **Step 4: Run parser/contract tests green**

  Run the focused tests and inspect artifact records for frozen hypothesis hashes and visible-file manifests.

### Task 4: Add bounded execution-feedback test instantiation without changing the evaluator

**Files:**
- Create: `scripts/generate_test_from_trigger.py`
- Create: `scripts/execute_experiment3.py`
- Modify: `tests/test_experiment3_contracts.py`

**Interfaces:**
- `generate_test_from_trigger.py` produces one complete pytest module from one frozen hypothesis and one trigger.
- `execute_experiment3.py` invokes the existing `run_test` and `classify_output` functions, writes buggy/fixed logs, hashes unchanged tests, and records at most two mechanical repair iterations.

- [ ] **Step 1: Add tests for unchanged execution and repair limits**

  Use temporary Python checkouts to assert the same test hash is used for both revisions, syntax/setup failures are not semantic F2P, and feedback cannot alter hypothesis/oracle fields or exceed two iterations.

- [ ] **Step 2: Run focused evaluator-adapter tests red**

  Run `pytest -q tests/test_experiment3_contracts.py -k execution`; expected failure is missing adapter.

- [ ] **Step 3: Implement the adapter and bounded repair bookkeeping**

  Reuse the current evaluator call path; do not edit `scripts/evaluate_experiment2.py` or `scripts/evaluate_generated_tests.py` classification semantics. Store test hashes, exits, classes, logs, repair count, and feedback category.

- [ ] **Step 4: Run focused tests green**

  Run the execution tests and verify the evaluator-only fixed checkout is only opened by the execution/evaluation process.

### Task 5: Prepare stored mechanism-matched hypotheses and run Experiment 3

**Files:**
- Create: `scripts/prepare_experiment3.py`
- Create: `results/experiment3_results.csv`
- Create: `results/experiment3_summary.md`
- Create: `results/experiment3_failure_analysis.md`
- Create: `results/experiment3_budget_analysis.md`
- Create: `results/experiment3_reviewer_report.md`
- Create: `results/trigger_research.md`
- Create: `results/trigger_intervention_design.md`
- Create: `artifacts/execution_logs/experiment3/`

**Interfaces:**
- Preparation exports stored C mechanism-matched hypotheses from existing Experiment 2 artifacts without exposing evaluator labels to the generation prompt.
- Result CSV has hypothesis-, trigger-, test-, execution-, and cost-level columns required by the brief.

- [ ] **Step 1: Add deterministic preparation tests**

  Assert conditional inputs are copied verbatim from stored artifacts and exclude fixed checkout, hidden truth, and post-execution labels from generation-visible records.

- [ ] **Step 2: Run preparation tests red**

  Run `pytest -q tests/test_experiment3_contracts.py -k preparation`; expected failure is missing preparation code.

- [ ] **Step 3: Implement preparation and report schemas**

  Derive 5 natural hypothesis seeds and all prior mechanism-matched conditional hypotheses from artifacts; record provenance and SHA-256 hashes.

- [ ] **Step 4: Run real generation and evaluation**

  Run harness verification, then run `python scripts/run_experiment3.py --mode natural --arm C1 --attempts 5`, the corresponding C2 run, and conditional runs if the API budget and stored hypotheses permit. Execute all generated tests against both revisions with the unchanged evaluator.

- [ ] **Step 5: Generate all reports from CSV/artifacts**

  Compute trigger executability, activation, mechanism-to-failure/F2P, diversity yield, unique failure modes, normalized cost metrics, and taxonomy counts without dropping failed attempts.

### Task 6: Update project documentation, verify, and commit

**Files:**
- Modify: `README.md`
- Modify: `FOLLOWUP_REPORT.md`
- Modify: `research_log.md`
- Create: `data/experiment3_case_manifest.json`
- Create: `results/experiment3_results.csv`

- [ ] **Step 1: Add documentation assertions**

  Extend existing documentation tests to require Experiment 3 artifacts, frozen-hypothesis language, budget-normalized interpretation, and explicit negative-result caveats.

- [ ] **Step 2: Run the full test suite**

  Run `pytest -q` and fix only genuine regressions.

- [ ] **Step 3: Run final verification commands**

  Run `python scripts/verify_harness.py`, `git diff --check`, and artifact schema checks; confirm `.env` and API-key material are absent from the diff.

- [ ] **Step 4: Commit the completed experiment**

  Stage only Experiment 3 source, tests, generated artifacts, reports, and docs; commit with `git commit -m "run experiment3 trigger construction follow-up"`.

