# Follow-up report

After the presentation feedback, I tested one uncertain assumption from the proposal: whether genuinely related historical bug experience can help discover a hidden target bug beyond target-only exploration or naive raw-history prompting.

Experiment 1 was inconclusive. Its raw baseline did not receive the transferable fix diff, the common prompt unintentionally encouraged raw history to abstain, structured fields were generic, and the target context omitted the locale facts that made the defect observable. The full audit is in `results/experiment1_audit.md`.

I then ran a smaller transfer-feasibility experiment on real BugsInPy `PySnooper:1`, whose buggy/fixed harness was independently verified. B and C received the same two historical bugs: `cookiecutter:1` (strong explicit-UTF-8 mechanism match) and `PySnooper:3` (weaker same-domain file-output analogue). A saw only the same bounded target context. The preserved prior batches used five attempts each; the new replication used ten new attempts per condition, with the same DeepSeek model/configuration, output budget, repair budget, and execution environment.

This is a retrospectively selected transfer-feasibility experiment. It evaluates whether the mechanism can transfer when suitable history is available. It does not evaluate autonomous retrieval quality.

The evaluator semantics were then audited. The original strict evaluator counted only assertion failures and incorrectly classified target-origin `UnicodeEncodeError` as mechanical. The corrected rule accepts either an assertion failure or a target exception that violates a pre-execution oracle, provided the unchanged test passes on fixed and setup is valid.

Final objective results after re-evaluation:

- Across 25 attempts per condition (15 preserved prior plus 10 new replication), A produced 0/25 F2P and 0 mechanism matches.
- B produced 0/25 F2P and 2 mechanism matches.
- C produced 2/25 verified `EXCEPTION_F2P` and 15 mechanism matches. Both valid F2P cases occurred in the preserved exploratory C batch and involved `UnicodeEncodeError` in target `pysnooper/tracer.py`, with the same tests passing on fixed.
- No assertion-based F2P occurred. The new 10-attempt replication produced no F2P; C had 6/10 mechanism matches, two F2F, and eight P2P.

The evaluator ran every unchanged generated test on both buggy and fixed revisions. The two exception-based F2P cases satisfy the corrected criterion: their hypotheses and target-supported oracles were present before execution, setup was valid, the exception occurred inside target behavior, and the fixed revision passed.

The honest conclusion is: in this retrospectively selected transfer-feasibility case, structured historical knowledge identified the correct failure mechanism and produced verified executable evidence distinguishing buggy and fixed revisions. The result is not architecture proof: the F2P cases occurred in one batch, later attempts did not reproduce them, and A/B did not produce valid F2P. Trigger construction remains the bottleneck.

Reviewer artifacts: `results/evaluator_audit.md`, `results/experiment2_replication2.csv`, `results/experiment2_replication2_summary.md`, `results/experiment2_cumulative_summary.md`, and `results/failure_analysis_final.md`.

Limitations: one target, 25 total attempts per condition, retrospective history selection, model output/JSON failures, no statistical inference, and no recall denominator.

## Experiment 3 trigger-construction follow-up

The selected intervention is a generic structured trigger planner: freeze a structured-history hypothesis, generate four meaningfully distinct trigger plans, instantiate one executable test per plan, and reuse the existing evaluator. This was chosen because Experiment 2 already localized the main bottleneck to `TRIGGER_TOO_WEAK`, `TRIGGER_WRONG_SHAPE`, P2P, and F2F outcomes. The research comparison and leakage boundary are recorded in `results/trigger_research.md` and `results/trigger_intervention_design.md`.

The implementation and contract tests were completed. The real harness still verifies buggy/fixed separation (`buggy=1`, `fixed=0`). Natural 3A produced no executable tests: 3 `NO_SUPPORTED_HYPOTHESIS` and 2 model-output errors. Conditional 3B kept five stored mechanism-matched hypotheses frozen. C1 generated 5 direct tests with 2 F2P, 1 F2F, and 2 P2P. C2 generated 8 executable trigger-tests with 3 F2P, 3 F2F, and 2 P2P after two bounded planner repairs; three hypotheses never yielded valid planner JSON. C2 used 20 LLM calls and 8 test pairs versus C1’s 5 calls and 5 pairs.

The complete status is in `results/experiment3_summary.md`, `results/experiment3_budget_analysis.md`, `results/experiment3_failure_analysis.md`, and `results/experiment3_reviewer_report.md`. The strongest conclusion is CASE C: diversification found one additional raw F2P, but F2P per hypothesis stayed at 40% and F2P per executed test fell from 40% to 37.5%. The next engineering change should target planner output validity and observable/assertion alignment; the evaluator should remain frozen.
