# History-Guided Bug Discovery PoC Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and execute a small reproducible A/B/C empirical study comparing target-only, raw historical evidence, and structured applicability-aware historical evidence on real buggy/fixed Python revisions.

**Architecture:** Keep the benchmark repository and evaluator-only truth data under `workspace/`, while generation-visible target context is materialized separately under `data/target_context/`. A deterministic Python runner will call the same DeepSeek model for each condition, write one hypothesis and one test per attempt, and evaluate unchanged tests against buggy and fixed checkouts. Historical cases are represented once as raw evidence and once as evidence-grounded structured units; condition C applies bounded applicability decisions and may emit `NO_SUPPORTED_HYPOTHESIS`.

**Tech Stack:** Python 3.13; Git; pytest; BugsInPy; `requests`; DeepSeek OpenAI-compatible HTTP API; JSON/CSV/Markdown artifacts; subprocess-based execution.

## Global Constraints

- Use real BugsInPy cases first and document every fallback.
- Never expose target issue, fix, regression test, fix diff, or evaluator-only metadata to generation.
- Conditions A/B/C receive the same target context, model, attempt count, token limit, repair budget, and runtime.
- Conditions B and C use the same historical case IDs.
- Never print, log, commit, or write the DeepSeek API key.
- Only meaningful semantic assertion failures count as failures; setup and mechanical failures are separate.
- Preserve exact generated tests and run the same file against buggy and fixed revisions.
- Record raw counts and limitations; do not claim statistical significance from the small PoC.

### Task 1: Prove the BugsInPy harness

**Files:**
- Create: `scripts/bootstrap_benchmark.py`
- Create: `data/case_manifest.json`
- Create: `artifacts/harness/`
- Create: `research_log.md`

**Interfaces:**
- `bootstrap_benchmark.py --case project:bug --root workspace/bugsinpy` clones the official repository, records tool versions and source revision, enumerates metadata, checks out buggy and fixed forms, and executes the benchmark regression test in both forms.
- The manifest stores exact project, bug ID, revisions, test command, and evaluator-only paths.

- [ ] **Step 1: Write the harness verifier test**

  Add `tests/test_manifest_schema.py` asserting the manifest has explicit buggy/fixed revisions, an executable test command, and no target issue/fix text in generation context.

- [ ] **Step 2: Run the schema test to verify the missing manifest failure**

  Run `pytest -q tests/test_manifest_schema.py`; expect a collection or assertion failure because the manifest is not populated yet.

- [ ] **Step 3: Implement the bootstrap script and run one official case**

  Clone `https://github.com/soarsmu/BugsInPy`, use its framework metadata/commands, capture stdout/stderr and exit codes, and select the first case whose buggy and fixed regression commands both execute in the host environment or documented Docker fallback.

- [ ] **Step 4: Verify the harness evidence**

  Run `python scripts/bootstrap_benchmark.py --self-check` and inspect the generated logs for distinct buggy/fixed outcomes and exact revisions.

### Task 2: Prepare historical and target-visible data

**Files:**
- Create: `scripts/prepare_data.py`
- Create: `data/historical_raw.json`
- Create: `data/historical_structured.json`
- Create: `data/target_context/`
- Create: `data/evaluator_truth/`

**Interfaces:**
- `prepare_data.py --manifest data/case_manifest.json` emits raw and structured historical records, bounded target context, and evaluator-only truth separately.
- Every structured field carries a `source` or `inferred` marker and evidence references.

- [ ] **Step 1: Write data-contract tests**

  Add tests that validate all required structured fields, shared historical IDs between raw and structured data, and absence of evaluator-only target fields from target context.

- [ ] **Step 2: Run the data-contract tests to verify red**

  Run `pytest -q tests/test_data_contract.py`; expect failure before generated data exists.

- [ ] **Step 3: Implement deterministic extraction**

  Read historical bug metadata, source diff, regression test, and repository context for 5–10 cases from at least two projects when available; write evidence-grounded summaries without fabricating unsupported fields. Extract target symbols/docs/tests using bounded file reads and Python AST where available.

- [ ] **Step 4: Run the data-contract tests green**

  Run `pytest -q tests/test_data_contract.py` and inspect both JSON files manually for evidence references and explicit inferred labels.

### Task 3: Implement the controlled DeepSeek pipelines

**Files:**
- Create: `scripts/deepseek_client.py`
- Create: `scripts/prompts.py`
- Create: `scripts/run_experiment.py`
- Create: `prompts/target_only.txt`
- Create: `prompts/raw_history.txt`
- Create: `prompts/structured_history.txt`
- Create: `generated_tests/`
- Create: `artifacts/llm/`

**Interfaces:**
- `DeepSeekClient.generate(prompt, max_tokens) -> response, usage, latency` reads `DEEPSEEK_API_KEY` only from the environment and logs metadata without secrets.
- `run_experiment.py --attempts 3 --conditions A,B,C` writes exactly one candidate per attempt and one test when executable; condition C may write `NO_SUPPORTED_HYPOTHESIS`.

- [ ] **Step 1: Write client and prompt contract tests**

  Test secret redaction, consistent model/configuration, exactly-one-hypothesis parsing, required oracle fields, and condition-C no-support parsing using mocked HTTP responses.

- [ ] **Step 2: Run contract tests red**

  Run `pytest -q tests/test_pipeline_contract.py`; expect failure before implementation.

- [ ] **Step 3: Implement the API client and fixed prompts**

  Use the official DeepSeek OpenAI-compatible endpoint semantics, bounded retries, timeout, request/usage/latency logs, and identical model settings. Put target context in all prompts; add only raw history for B and the same IDs as structured units plus applicability instructions for C.

- [ ] **Step 4: Implement candidate/test parsing and repair budget**

  Enforce one hypothesis and one test, allow at most two mechanical repairs, reject `assert False`, mocks that manufacture failures, Git access, fixed-revision references, benchmark metadata access, and unsupported oracle claims.

- [ ] **Step 5: Run contract tests green**

  Run `pytest -q tests/test_pipeline_contract.py` and inspect redacted logs.

### Task 4: Execute objective buggy/fixed evaluation

**Files:**
- Create: `scripts/evaluate_generated_tests.py`
- Create: `results/results.csv`
- Create: `results/summary.csv`
- Create: `results/failure_analysis.md`
- Create: `artifacts/execution_logs/`

**Interfaces:**
- `evaluate_generated_tests.py` runs each unchanged generated test in the exact buggy and fixed checkouts and classifies F2P, P2P, F2F, P2F, or MECHANICAL_FAILURE.
- `results.csv` contains condition, target, attempt, hypothesis/test status, buggy/fixed outcome, oracle support, failure layer, repair count, model usage, latency, and log paths.

- [ ] **Step 1: Write evaluator tests**

  Add tests using tiny local temporary repositories to verify unchanged-test execution, meaningful assertion classification, mechanical-error exclusion, and F2P labeling.

- [ ] **Step 2: Run evaluator tests red**

  Run `pytest -q tests/test_evaluator.py`; expect failure before implementation.

- [ ] **Step 3: Implement isolated checkout execution**

  Copy generated tests into clean buggy/fixed worktrees, run with identical environment and timeout, record stdout/stderr/exit code, and classify outcomes according to the brief.

- [ ] **Step 4: Execute the small study**

  Run three attempts per condition per usable target, or five per condition if only one target survives harness verification. If the API is unavailable, execute the documented module-level fallback using the same real historical records.

- [ ] **Step 5: Generate raw summaries and failure analysis**

  Aggregate counts without inferential statistics and classify every unsuccessful attempt into the required failure layers.

### Task 5: Document and verify the PoC

**Files:**
- Create: `README.md`
- Create: `FOLLOWUP_REPORT.md`
- Modify: `research_log.md`

**Interfaces:**
- README contains exact reproduction commands, data split, leakage controls, prompts/config, metrics, results, one detailed case, limitations, and honest conclusion.
- FOLLOWUP_REPORT is a concise reviewer-facing memo beginning with the presentation-feedback framing requested by the brief.

- [ ] **Step 1: Write documentation checks**

  Add `tests/test_reproducibility_docs.py` asserting required files, commands, conditions, classifications, and limitation language are present.

- [ ] **Step 2: Run documentation checks red**

  Run `pytest -q tests/test_reproducibility_docs.py`; expect failure before final docs exist.

- [ ] **Step 3: Write evidence-backed reports**

  Use only generated artifacts and execution logs for counts and claims; explicitly state retrospective historical selection and the absence of autonomous retrieval validation.

- [ ] **Step 4: Run the full verification suite**

  Run `pytest -q`, rerun the experiment/evaluator from a clean output directory if feasible, confirm the output files are populated, and inspect `git diff --check`.

- [ ] **Step 5: Commit the reproducible repository**

  Run `git add` on the experiment artifacts and `git commit -m "build empirical history-guided bug discovery poc"`; verify the commit does not include `.env` or secrets.
