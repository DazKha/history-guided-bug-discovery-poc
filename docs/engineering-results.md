# Engineering Results

This report records the engineering journey from naive prompting to structured historical knowledge and then to a downstream trigger-construction refinement. The evidence is preserved in machine-readable artifacts; no new generation run is performed by the verification commands.

## 1. Initial problem

Historical issue reports contain useful debugging knowledge, but they are noisy and difficult to transfer directly to a new target. The question was whether a structured, mechanism-level representation would help an agent identify the relevant failure mechanism better than naive baselines.

The transfer-feasibility case is BugsInPy `PySnooper:1`, with a checked buggy/fixed revision pair. The case and history subset were selected retrospectively to test whether suitable history could transfer; retrieval quality and broad generalization are outside this POC.

## 2. Naive baselines

The controlled comparison uses:

- **A — Target only:** the bounded target context without historical cases.
- **B — Raw history:** the target context plus the selected historical issue material in raw form.
- **C — Structured history:** the target context plus the same underlying historical cases converted into mechanism-oriented knowledge and an applicability decision.

The protocol keeps target context, model/configuration, runtime, evaluator policy, and comparable attempt budget aligned across conditions. The clean replication is the two preserved five-attempt halves in `results/experiment2_replication2.csv`, giving ten attempts per condition.

## 3. Structured-history intervention

The structured records organize historical evidence around context, preconditions, trigger, expected invariant, observed failure, failure mechanism, oracle provenance, test strategy, evidence references, and confidence. This representation is intended to make the transferable mechanism explicit rather than asking the model to infer it from a long raw issue or patch.

The implementation currently uses prepared structured records and fixed prompt strategies. It does not learn a retrieval index or autonomously select history.

## 4. Controlled result

The clean replication is derived from `results/experiment2_replication2.csv`:

| Condition | Mechanism matches | Attempts | Verified F2P |
| --- | ---: | ---: | ---: |
| A — Target only | 0 | 10 | 0 |
| B — Raw history | 1 | 10 | 0 |
| C — Structured history | 6 | 10 | 0 |

The source mapping is explicit:

- Mechanism match: `hypothesis_matches_true_failure_mechanism == "yes"`.
- Verified F2P: `verified_f2p == "True"`; blank values are non-F2P because no verified result exists.
- Conditions: `A/TARGET_ONLY`, `B/NAIVE_RAW_HISTORY`, and `C/STRUCTURED_APPLICABILITY_AWARE`.
- Clean replication: `run_label == "replication2"` with source batches `replication2b` and `replication2c`.

The result supports a narrow engineering conclusion: structured history improved mechanism targeting in this selected transfer-feasibility case. It does not establish that structured history alone produces more executable differential tests.

## 5. What improved

The cumulative file `results/experiment2_re_evaluated.csv` combines the preserved batches and is supporting evidence:

| Condition | Mechanism matches | Attempts | Verified F2P |
| --- | ---: | ---: | ---: |
| A — Target only | 0 | 25 | 0 |
| B — Raw history | 2 | 25 | 0 |
| C — Structured history | 15 | 25 | 2 |

The structured condition retained the mechanism-match advantage across the cumulative record. The two verified F2P rows are both exploratory structured-history cases and are valid buggy/fixed differential outcomes under the recorded evaluator rule.

## 6. What did not improve

The clean replication produced zero F2P in every condition. The cumulative F2P cases did not reproduce in the clean replication batch. This separates two stages that should not be conflated:

1. identify the likely failure mechanism;
2. construct a valid precondition, state/action sequence, observable, and assertion that exposes it.

The data support improvement in the first stage, not a stable F2P improvement claim in the second.

## 7. Root-cause diagnosis

The failure pattern localized the remaining instability to executable trigger construction. Correct or plausible mechanism hypotheses still yielded weak triggers, wrong-shaped tests, model-output failures, or assertions that did not align with the observable behavior. Mechanical/setup failures are not counted as semantic F2P.

The evaluator was kept fixed for the later engineering work. The strongest signal remains an unchanged test that fails semantically on the buggy revision and passes on the fixed revision.

## 8. Trigger Plan refinement

Experiment 4 added a strict Trigger Plan contract inside executable-test generation. The plan makes preconditions, initial state, actions, observable, assertion, and timeout explicit; deterministic validation rejects incomplete or evaluator-leaking plans; bounded repair addresses invalid planner output.

The downstream comparison found:

- valid plans improved from 2/5 hypotheses to 5/5;
- hypotheses with at least one F2P improved from 3/5 for direct generation to 4/5 for the planner under the budget-matched comparison;
- direct generation remained more efficient per generated test.

This is an engineering reliability result. It does not replace or supersede the structured-history contribution, and it does not support a per-test trigger-efficiency improvement claim. Full Experiment 4 evidence remains in `docs/experiment4-report.md` and the `results/experiment4_*` artifacts.

## 9. Current implementation status

Implemented:

- leakage-separated target context and evaluator-only manifest;
- raw and structured historical evidence records;
- A/B/C generation prompt contracts;
- frozen hypothesis and test artifact handling;
- buggy/fixed differential evaluation;
- strict Trigger Plan validation and bounded repair;
- deterministic core and downstream evidence verification;
- offline replay and execution logs.

Partially implemented:

- structured history preparation is present, but history selection is retrospective;
- the proposed memory concepts are represented in data, not learned or retrieved autonomously;
- the trigger planner is implemented as a downstream refinement for the selected workflow.

Proposed future extension:

- evaluate retrieval and structured-history construction across additional independently selected targets, with a pre-registered protocol and no target-evaluator leakage.

## 10. Limitations

This is one selected target and one retrospectively selected transfer-feasibility case with small attempt counts. It has no statistical significance analysis, no recall denominator, and no broad cross-project generalization claim. The clean replication is evidence about mechanism targeting under this protocol, not a universal ranking of prompting methods.

## 11. Next engineering step

The next step is to improve trigger construction while keeping the structured-history comparison and evaluator frozen: make observable/assertion alignment more robust, preserve strict plan validation, and evaluate any change against a newly specified held-out set rather than changing the recorded evidence.
