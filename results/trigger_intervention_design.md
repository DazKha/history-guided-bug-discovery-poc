# Experiment 3 trigger intervention design

## Chosen intervention

Freeze one structured-history hypothesis and generate four structured, semantically distinct trigger plans before generating executable tests. Each plan records preconditions, input mutation, state setup, environment setup, action sequence, observable, rationale, target evidence, and confidence. A deterministic filter removes exact semantic duplicates. The existing evaluator then runs every unchanged retained test on buggy and fixed revisions.

## Why this is the smallest useful change

Experiment 2 already shows that structured history can identify the failure mechanism. The new stage changes only the conversion from mechanism to concrete conditions. It does not change retrieval, historical representation, target context, model family, oracle policy, or evaluator semantics. N=4 is large enough to test meaningful diversity and small enough to expose execution cost.

## Arms

| Arm | Pipeline | Purpose |
|---|---|---|
| C1 | frozen structured-history hypothesis → one direct test | Existing trigger construction baseline |
| C2 | same frozen hypothesis → planner → four trigger candidates → one test/candidate | Trigger diversification intervention |

Natural mode generates the hypothesis pool once and shares it between C1 and C2. Conditional mode uses previously stored C mechanism-matched hypotheses verbatim; it never regenerates or rewrites them.

## Frozen variables

- PySnooper:1 buggy/fixed revisions and execution environment.
- Same target context and same two structured historical units.
- Same model and temperature when the model is available.
- Same oracle support policy and exception-aware evaluator.
- Same test timeout and repair budget.
- Same visible-file manifest and leakage rules.

## Leakage controls

Generation-visible inputs contain only the buggy target context, structured history, frozen hypothesis, and trigger/test prompt. The fixed checkout, target issue, fix diff, hidden regression test, changed-file metadata, evaluator truth, mechanism-match labels, and post-execution classification are evaluator-only. Trigger planning is generic and does not encode PySnooper-specific facts.

## Feedback boundary

If enabled, feedback may revise syntax, imports, fixtures, setup mechanics, or execution path. It may not change the frozen hypothesis, expected behavior, oracle, or target. The maximum is two iterations; the implemented run records repair count and feedback category.

## Status of this run

The real model run completed after robustly parsing the repository `.env` format without printing or storing the secret. Natural 3A produced five hypothesis-stage responses but no executable tests. Conditional 3B generated five direct C1 tests and eight executable C2 trigger-tests after two bounded planner repairs; three hypotheses remained planner-invalid and were retained in the accounting. The evaluator was unchanged.
