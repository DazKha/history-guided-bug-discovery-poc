# Reviewer Usability Refactor Design

## Goal

Make the committed history-guided bug-discovery PoC understandable and runnable from a fresh clone without changing its historical evidence, v1 evaluator, prompts used for historical generation, or model settings.

## Scope

The refactor is documentation-led with two small safety/usability changes:

1. Replace the long README with a reviewer path that distinguishes preserved offline verification, preserved downstream replay, new Experiment 2 generation, and the external buggy/fixed harness.
2. Add `docs/code-map.md` mapping A/B/C inputs, prompt assembly, artifacts, and evaluators.
3. Add a read-only Experiment 2 prompt renderer that uses the committed `run_experiment2.py` prompt construction, prints the SHA-256 hash, and refuses to overwrite or write inside experiment artifact directories.
4. Make a live Experiment 2 run require a non-empty safe run label and refuse to use an existing artifact/test output directory.
5. Remove the live runner's `write_templates()` side effect because the `prompts/experiment2_*.md` files are pointers, not executable prompt sources, and no committed code or verification depends on them being rewritten.

No experiment is run. No preserved artifact, generated test, CSV, evaluator, model setting, or target checkout is changed.

## Prompt and evidence model

The actual Experiment 2 generation prompt remains in `scripts/run_experiment2.py`, assembled by `base_instructions()` and `prompt_for()`. Condition C continues to receive structured history plus explicit applicability-aware instructions. The renderer reports that it is rendering the current committed construction; it does not claim byte-for-byte reproduction of an historical request unless the request was preserved.

The v1 result table is described as the existing rule-based mechanism-related signal. Its implementation is documented accurately: it looks for at least one encoding-related token and at least one target-related token in the hypothesis/trigger/failure/test/oracle text. It is not an independent validation of a complete causal mechanism.

## Verification

The behavioral change is covered by tests for safe run labels, refusal to reuse an existing Experiment 2 output directory, renderer hashes/output protection, and prompt-source traceability. The final verification includes the full test suite, core-result verification, Experiment 4 artifact verification, both preserved replay arms, Markdown/path checks, `git diff --check`, evidence immutability checks, and remote-head verification after push.
