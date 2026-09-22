# Follow-up report

After the presentation feedback, I tested one uncertain assumption from the proposal: whether genuinely related historical bug experience can help discover a hidden target bug beyond target-only exploration or naive raw-history prompting.

Experiment 1 was inconclusive. Its raw baseline did not receive the transferable fix diff, the common prompt unintentionally encouraged raw history to abstain, structured fields were generic, and the target context omitted the locale facts that made the defect observable. The full audit is in `results/experiment1_audit.md`.

I then ran a smaller transfer-feasibility experiment on real BugsInPy `PySnooper:1`, whose buggy/fixed harness was independently verified. B and C received the same two historical bugs: `cookiecutter:1` (strong explicit-UTF-8 mechanism match) and `PySnooper:3` (weaker same-domain file-output analogue). A saw only the same bounded target context. All conditions used five attempts, the same DeepSeek model/configuration, output budget, repair budget, and execution environment.

This is a retrospectively selected transfer-feasibility experiment. It evaluates whether the mechanism can transfer when suitable history is available. It does not evaluate autonomous retrieval quality.

Final objective results:

- A target-only: 5 tests, 0 mechanism matches, 0 F2P, 5 P2P.
- B naive raw history: 4 tests, 0 mechanism matches, 0 F2P, 4 P2P, 1 model/JSON error.
- C structured + applicability: 3 tests, 2 mechanism matches, 0 F2P, 2 P2P, 1 F2F, 2 model/JSON errors.

The evaluator ran every unchanged generated test on both buggy and fixed revisions. No condition achieved the required assertion-level `T(B)=FAIL, T(F)=PASS` result. A preserved exploratory pass did produce an encoding-focused C test that raised `UnicodeEncodeError` on buggy and passed on fixed, but it was not promoted to F2P because the expected target exception escaped instead of causing an intended semantic assertion failure.

The honest conclusion is: structured history improved mechanism targeting in this selected case, but this PoC did not verify a discovery advantage. The dominant remaining bottleneck was executable oracle/test construction, not harness reproducibility. The result is evidence for a refined next experiment, not proof that the architecture works.

Reviewer artifacts: `results/experiment2_summary.csv`, `results/experiment2_failure_analysis.md`, `results/experiment2_case_study.md`, and `results/experiment2_comparison_with_experiment1.md`.

Limitations: one target, five attempts per condition, retrospective history selection, model output/JSON failures, no statistical inference, and no recall denominator.
