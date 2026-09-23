# Experiment 4 reviewer report

## Review verdict

**Conditionally acceptable as a negative/mixed empirical result.** The experiment answered the intended bottleneck question without changing the historical-memory representation or evaluator. The evidence supports a planner-validity improvement and a hypothesis-coverage improvement, but not a normalized efficiency improvement.

## Strengths

- The five hypotheses were frozen and reused across all three refinements.
- C1 and C2 used the same model family, temperature, target context, structured history, oracle policy, and evaluator.
- The fixed checkout was accessed only through evaluation.
- Invalid planner responses, repair attempts, model errors, mechanical failures, P2P, F2F, and F2P outcomes were retained.
- The budget-matched direct arm prevents the raw C2 F2P count from being mistaken for per-test improvement.
- The strict validator is target-agnostic; it does not contain PySnooper-specific encoding or path rules.

## Limitations

- Five hypotheses are too few for statistical significance.
- The C2 plan prompt repeats a large target context and costs substantially more tokens than direct generation.
- The final intervention combines schema validation with a compact test-generation prompt and AST preflight; the exact contribution of each component is not separately randomized.
- The budget-matched C1 control has three direct generations per hypothesis, while C2 has three plans from one planner response plus one possible repair. This is execution-budget matched, not call-budget matched.
- The validator's lexical assertion alignment is a useful guard, not a semantic proof that an assertion is revision-discriminating.

## Threats checked

- Harness distinction: passed (`buggy=1`, `fixed=0`).
- Repository tests: passed (`24 passed` after Experiment 4 contract tests were added).
- Leakage: planner/generator prompts expose only buggy target context, structured history, and frozen hypothesis; no fixed source, patch, issue, regression test, or evaluator verdict is included.
- Evaluator manipulation: none; Experiment 4 reuses the existing classification functions.
- Cherry-picking: none; all raw rows and generated artifacts are preserved.

## Reviewer conclusion

The strongest supported statement is: **a strict, generic trigger-plan contract with bounded repair can eliminate most planner-output invalidity and can improve the chance that at least one candidate per frozen mechanism reaches F2P, but the present implementation does not improve F2P efficiency and remains vulnerable to generated-test setup and observation failures.**

The next experiment should add generic pre-execution collection/runtime validation with one bounded repair and measure whether mechanical failures decline, while keeping the current plan contract and all controls fixed.
