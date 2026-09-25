# Reviewer Usability Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the public PoC easy to review and safe to run while preserving all historical evidence and v1 results.

**Architecture:** Keep the existing Experiment 2 runner and prompt functions as the source of truth. Add a small read-only renderer around them, guard new runner output roots before any model call, and route reviewers from a concise README to a code map and existing detailed reports.

**Tech Stack:** Python 3.12, argparse, hashlib, pytest, Markdown, existing package CLI.

## Global Constraints

- Work only in the fresh clone of `origin/master`.
- Do not copy files from another checkout.
- Do not run a new experiment or change prompts/model settings used to interpret historical results.
- Preserve frozen hypotheses, model outputs, generated tests, execution logs, replay bundles, manifests, reports, and original v1 CSVs.
- Offline verification and replay must not require `DEEPSEEK_API_KEY`.
- New live Experiment 2 runs must use a new safe run label and refuse existing output roots.

---

### Task 1: Add failing behavioral tests for fresh-run safety and prompt rendering

**Files:**
- Modify: `tests/test_experiment2_contracts.py`
- Create: `tests/test_render_experiment2_prompt.py`

**Interfaces:**
- Tests will import `validate_run_label`, `ensure_fresh_run_paths`, and `render_prompt` from `scripts.run_experiment2` / `scripts.render_experiment2_prompt`.

- [ ] **Step 1: Write failing tests**

Add tests that prove:

```python
def test_run_label_rejects_path_traversal_and_empty_values():
    with pytest.raises(ValueError):
        validate_run_label("")
    with pytest.raises(ValueError):
        validate_run_label("../reuse")


def test_new_experiment2_run_refuses_existing_output_root(tmp_path):
    output_root = tmp_path / "artifacts"
    test_root = tmp_path / "tests"
    output_root.mkdir()
    with pytest.raises(ValueError, match="refusing to reuse"):
        ensure_fresh_run_paths(output_root, test_root)
```

The renderer tests must assert that `render_prompt("C", 1, root=ROOT)` contains the structured-history and applicability instructions, returns a 64-character SHA-256 hash, and does not create files. A separate test must show an explicit existing `--output` path is rejected rather than overwritten.

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
. .venv/bin/activate
python -m pytest -q tests/test_experiment2_contracts.py tests/test_render_experiment2_prompt.py
```

Expected: failure because the safety helpers, renderer, and renderer module do not yet exist.

### Task 2: Implement safe Experiment 2 prompt rendering and live-run guards

**Files:**
- Modify: `scripts/run_experiment2.py`
- Create: `scripts/render_experiment2_prompt.py`

**Interfaces:**
- `validate_run_label(label: str) -> str` accepts only a non-empty single path component matching `[A-Za-z0-9][A-Za-z0-9_.-]*`.
- `ensure_fresh_run_paths(output_root: Path, test_root: Path) -> None` raises `ValueError` if either path exists.
- `render_prompt(condition: str, attempt: int, root: Path = ROOT) -> tuple[str, str]` loads the committed Experiment 2 inputs, calls `prompt_for`, and returns `(prompt, sha256_hex)` without writing files.
- Renderer CLI options are `--condition A|B|C`, `--attempt POSITIVE_INT`, and optional `--output PATH`; existing output files and paths below `artifacts/` or `generated_tests/` are rejected.

- [ ] **Step 1: Implement the minimal helpers**

Add the label validation and two-root existence guard to `scripts/run_experiment2.py`. Make `--run-label` required in its CLI, validate it before constructing `DeepSeekClient`, and call the guard before creating either output directory. Remove `write_templates()` and its call; the runner must not rewrite pointer files during a live run.

- [ ] **Step 2: Implement the read-only renderer**

The renderer must import `CONDITIONS`, `ROOT`, and `prompt_for`, load `data/experiment2_target_context/PySnooper-1.txt`, `data/experiment2_historical_raw.json`, and `data/experiment2_historical_structured.json`, and print:

```text
Prompt source: current committed scripts/run_experiment2.py
Condition: C (STRUCTURED_APPLICABILITY_AWARE)
Attempt: 1
SHA256: <64 lowercase hex characters>

<assembled prompt>
```

When `--output` is provided, write only that requested prompt file after checking that it is not inside the repository's `artifacts/` or `generated_tests/` directories and does not already exist. The renderer must never instantiate the LLM client or create experiment directories.

- [ ] **Step 3: Run focused tests and verify GREEN**

Run:

```bash
python -m pytest -q tests/test_experiment2_contracts.py tests/test_render_experiment2_prompt.py
python scripts/render_experiment2_prompt.py --condition C --attempt 1 > /tmp/experiment2-prompt-render.txt
```

Expected: focused tests pass; the renderer exits 0, prints the source marker and SHA-256, and writes no repository artifact.

### Task 3: Add the reviewer code map and rewrite README

**Files:**
- Create: `docs/code-map.md`
- Modify: `README.md`
- Modify: `tests/test_reproducibility_docs.py`

**Interfaces:**
- README quickstart commands must be runnable from the repository root and distinguish offline verification, preserved replay, new LLM generation, packaged downstream run, and external harness.
- `docs/code-map.md` must map each A/B/C condition from entry point through prompt construction, visible inputs, output artifacts, and result/evaluator paths.

- [ ] **Step 1: Write documentation-contract tests**

Extend the documentation tests to require the README headings/phrases for scope, quickstart, A/B/C inspection, prompt/input/artifact locations, v1 metric definition, limitations, and detailed docs. Require `docs/code-map.md`, the renderer command, the new run-label command, and an explicit statement that offline verification/replay do not call the model.

- [ ] **Step 2: Run documentation tests and verify RED**

Run:

```bash
python -m pytest -q tests/test_reproducibility_docs.py
```

Expected: failure against the current long README because the new reviewer structure and code map are not yet present.

- [ ] **Step 3: Write the concise README and code map**

README order:

1. Scope and actual implementation boundary.
2. One compact pipeline.
3. Quickstart commands near the top.
4. A/B/C comparison and unchanged clean result table (`0/10`, `1/10`, `6/10`).
5. Prompt/input/code/artifact/result locations.
6. v1 metric definition and interpretation warning.
7. Limitations and detailed-document links.

Use the current runner and verifier names exactly. State that C combines structured history with applicability-aware instructions, that the Experiment 2 `.md` files are pointers, and that the renderer is current-code output rather than proven historical byte-for-byte prompt reproduction. Include one hypothesis trace using `data/experiment3_conditional_hypotheses.json`, `artifacts/experiment4/iteration3/hypotheses/`, an arm artifact, and `evidence-rows.csv`.

The code map must include older `scripts/run_experiment.py` and legacy `.txt` prompt fragments as preserved but non-authoritative provenance, and must identify downstream Trigger Plan prompts in `src/history_guided_bug_discovery/application/prompts.py`.

- [ ] **Step 4: Run documentation tests and verify GREEN**

Run:

```bash
python -m pytest -q tests/test_reproducibility_docs.py
```

Expected: PASS with no evidence files modified.

### Task 4: Verify the complete refactor and evidence immutability

**Files:**
- No additional production files; inspect the complete diff.

- [ ] **Step 1: Run the complete repository verification**

Run:

```bash
python -m compileall scripts tests
python -m pytest -q
python scripts/verify_core_results.py
python scripts/verify_experiment4_artifacts.py
replay --config configs/experiment4.json --artifacts artifacts/experiment4/iteration3 --arm C2
replay --config configs/experiment4.json --artifacts artifacts/experiment4/iteration3 --arm C1_BUDGETED
python scripts/verify_harness.py
```

Expected: all commands except the harness complete successfully; harness failure is reported only as the exact missing-checkout prerequisite. Replay must remain API-key free.

- [ ] **Step 2: Check docs, links, and evidence paths**

Run a Markdown/path script that resolves every local Markdown link and every backtick path in `README.md` and `docs/code-map.md`, excluding documented external prerequisites and shell placeholders. Run `git diff --check` and inspect the diff for only README/docs/renderer/tests/safety changes.

- [ ] **Step 3: Confirm evidence immutability and repository state**

Compare SHA-256 values for `results/experiment2_replication2.csv`, `results/experiment2_re_evaluated.csv`, `results/experiment4_iteration3_raw.csv`, `results/experiment4_iteration3_raw_budgeted.csv`, and all tracked `artifacts/`/`generated_tests/` files against their pre-edit values. Confirm no local evaluator-audit files were added and `git status --short` contains only intended refactor files.

- [ ] **Step 4: Commit the scoped refactor**

Run:

```bash
git add README.md docs/code-map.md scripts/run_experiment2.py scripts/render_experiment2_prompt.py tests/test_experiment2_contracts.py tests/test_render_experiment2_prompt.py tests/test_reproducibility_docs.py
git commit -m "docs: make history-guided poc reviewer-runnable"
```

- [ ] **Step 5: Push and verify remote head**

Run:

```bash
git push origin master
git fetch origin master
test "$(git rev-parse HEAD)" = "$(git rev-parse origin/master)"
```

Report the local starting hash, final hash, GitHub commit URL, tests/replays, missing harness prerequisite, unchanged evidence, and files removed (none unless a deletion is later proven safe).
