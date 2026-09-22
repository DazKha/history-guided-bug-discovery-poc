# Failure analysis

This file classifies every non-F2P cell from the final fifteen-attempt run.

| Cell | Outcome | Layer | Evidence |
|---|---|---|---|
| A/1 | MECHANICAL_FAILURE | MECHANICAL_EXECUTION | The generated test used an invalid watch expression and raised `SyntaxError` in both revisions. |
| A/2–A/4 | P2P | SEMANTIC_NON_TRIGGER | Three generated behavior tests passed in both revisions. |
| A/5 | NO_SUPPORTED_HYPOTHESIS | TARGET_CONTEXT | The target-only condition abstained without an executable candidate. |
| B/1–B/5 | NO_SUPPORTED_HYPOTHESIS | HISTORY_DISTRACTION | Raw history produced no executable candidate in five attempts. |
| C/1–C/5 | NO_SUPPORTED_HYPOTHESIS | APPLICABILITY | The structured condition explicitly returned `NOT_APPLICABLE` in five attempts. |

There were no dependency/import failures in the final generated-test evaluation. The only F2P-like FAIL/PASS result is the benchmark’s known PySnooper harness regression, which is not a generated test and is therefore not part of the A/B/C discovery counts.
