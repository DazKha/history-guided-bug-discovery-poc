# Experiment 1 audit

## Scope and evidence inspected

This audit was completed before changing any Experiment 1 prompts or data. It inspected `results/results.csv`, `results/summary.csv`, `results/failure_analysis.md`, the six raw and structured historical records, all A/B/C model artifacts, generated tests and execution logs, `data/case_manifest.json`, `data/target_context/PySnooper-1.txt`, and evaluator-only target truth.

## 1. Target and actual hidden defect

The target was BugsInPy `PySnooper:1`:

- buggy commit: `e21a31162f4c54be693d8ca8260e42393b39abd3`
- fixed commit: `56f22f8ffe1c6b2be4d2cf3ad1987fdb66113da2`
- evaluator-only regression: `tests/test_chinese.py::test_chinese`

The fix changes two implicit text-encoding sites in `pysnooper/tracer.py`: source bytes are decoded with explicit UTF-8 instead of ASCII, and `FileWriter.write` opens the output file with explicit UTF-8 instead of the process locale default. Under the experiment’s `LC_ALL=C`, `PYTHONUTF8=0`, Python 3.9 runtime, the buggy regression fails with `UnicodeEncodeError` while writing the Chinese characters `失败`; the fixed revision passes. The hidden mechanism is therefore locale-dependent implicit text encoding in real file/source I/O. The benchmark harness logs prove this B/F distinction independently of the LLM.

## 2. Historical cases supplied

The raw and structured conditions received the same six IDs:

`PySnooper:2`, `PySnooper:3`, `cookiecutter:1`, `cookiecutter:2`, `cookiecutter:3`, and `cookiecutter:4`.

Transfer compatibility is mixed, not uniform:

| Historical case | Relation to target mechanism | Evidence-backed judgment |
|---|---|---|
| `cookiecutter:1` | Strong | Fix changes `open(context_file)` to `open(context_file, encoding='utf-8')` and adds a non-ASCII JSON fixture. This is the same explicit-encoding-vs-locale mechanism, though the read path differs from PySnooper’s write/source paths. |
| `PySnooper:3` | Partial | It changes a file-output path and a writer call, but the recorded diff does not establish the same encoding defect; it is weaker than `cookiecutter:1`. |
| `PySnooper:2` | Weak/unrelated | Custom representation tuple support; no encoding transfer evidence. |
| `cookiecutter:2` | Unrelated | Multiple hook discovery/execution. |
| `cookiecutter:3` | Unrelated | Click prompt rendering. |
| `cookiecutter:4` | Unrelated | Hook failure exception and cleanup behavior. |

Thus Experiment 1 did contain one strong historical transfer case, but it was diluted by five other cases and was not surfaced in a concise mechanism-centered representation.

## 3. Raw RAG behavior

Raw RAG was unintentionally allowed to abstain too easily. The shared prompt told every condition to “Prefer `NO_SUPPORTED_HYPOTHESIS` when the oracle is unsupported.” This instruction was applied to B even though the naive baseline was supposed to generate its best plausible target-specific hypothesis without an explicit applicability gate.

More importantly, `compact_raw()` supplied only IDs, commit subjects, generic fix summaries, regression-test summaries, and source references. It did not include the stored raw `evidence.fix_diff` or regression-test source. Consequently, B did not actually see the strongest historical signal from `cookiecutter:1`: the explicit `encoding='utf-8'` change. The model’s repeated explanations—“no target-specific bug report” and “no supported oracle”—are consistent with this input loss, not evidence that raw history cannot transfer.

## 4. Structured applicability behavior

C received more information than B, including truncated diff text, but the structured fields were too generic for mechanism transfer. For every case, `Expected Invariant` was essentially “the behavior asserted by the historical regression test should hold,” and `Oracle Provenance` explicitly emphasized that the historical oracle was insufficient for target truth. `Failure Mechanism` was a large diff excerpt rather than a concise semantic statement such as “implicit locale decoding/encoding is replaced by explicit UTF-8.”

The common prompt also strongly emphasized abstention and said that historical invariants alone could not confirm target truth. That is appropriate as a safety rule, but the prompt did not ask C to separately score mechanism similarity, trigger similarity, invariant similarity, and target-side support. All five C outputs were bare `NOT_APPLICABLE` decisions with no reasons. Because `cookiecutter:1` is retrospectively known to share the target’s explicit-encoding mechanism, these outputs are best classified as over-conservative applicability decisions for this feasibility setup rather than proof of non-transferability.

## 5. Target-context sufficiency

The target context was not empty: it contained README material, `pysnooper/tracer.py`, `variables.py`, `utils.py`, setup/configuration, and ordinary tests. It visibly contained the relevant buggy lines: `encoding = 'ascii'` and `open(self.path, 'w' if ... else 'a')`.

However, two details weakened the experiment:

1. `tracer.py` and `tests/test_pysnooper.py` were truncated at the global 45,000-character context cap.
2. The runtime facts that made the defect observable—Python 3.9 plus `LC_ALL=C`, `PYTHONUTF8=0`, and `PYTHONCOERCECLOCALE=0`—were recorded in the manifest but not included in the LLM prompt.

The model therefore saw a plausible implementation but not the cross-platform execution condition that turns implicit encoding into a falsifiable target behavior. The context was adequate for ordinary API hypotheses, which explains the A P2P tests, but weak for this particular transfer oracle.

## 6. Test-generation and execution diagnosis

Condition A generated four tests across five attempts: three P2P tests of already-working behavior and one mechanical test using an invalid watch expression that raised `SyntaxError` on both revisions. It generated no meaningful buggy failure. B and C generated no tests because they abstained before test generation; there was no evidence that their test repair or execution mechanics caused the negative result.

The failed A test was correctly excluded as `MECHANICAL_FAILURE`; the three P2P tests were correctly classified as `SEMANTIC_NON_TRIGGER`. The absence of F2P is therefore a hypothesis/oracle/context failure, not an evaluator failure.

## 7. Root-cause conclusion

The first experiment is inconclusive about positive historical transfer. The strongest evidence points to four interacting design problems:

1. **History mismatch/dilution:** only `cookiecutter:1` was strongly transferable; five cases were unrelated.
2. **Raw representation loss:** B did not receive the raw fix diff that contained the transferable mechanism.
3. **Prompt confound:** the abstention instruction intended for C was applied to B and, through the common prompt, also made A conservative.
4. **Context gap:** the target runtime locale was not visible, and relevant files were truncated.

This is not sufficient evidence to reject the structured-history idea or the overall architecture. The smallest fair follow-up is a retrospectively selected transfer-feasibility study using the same PySnooper target, `cookiecutter:1` plus one partial PySnooper file-output case, a full mechanism-centered target context, raw B evidence that actually includes the fix diff, and an applicability gate only in C.
