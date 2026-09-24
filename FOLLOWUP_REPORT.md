# Engineering Outcome Report

## 1. Initial problem

Raw issue history contains useful debugging knowledge, but it is noisy and difficult to transfer directly to a new target. This prototype asks whether structured, mechanism-level historical knowledge helps an agent identify the relevant failure mechanism better than naive baselines.

The study uses the selected BugsInPy `PySnooper:1` transfer-feasibility case. History selection was retrospective, so the result does not measure autonomous retrieval or broad generalization.

## 2. Naive baselines

The controlled comparison uses the same target, model/configuration, execution environment, evaluator policy, and comparable attempt budget:

- **A — Target only**
- **B — Target plus raw historical issue context**
- **C — Target plus structured historical knowledge**

B and C use the same underlying historical cases. C adds mechanism-oriented fields and an applicability decision.

## 3. Structured-history intervention

Historical records were reorganized around context, preconditions, trigger, expected invariant, observed failure, failure mechanism, oracle provenance, test strategy, and evidence references. The intent was to make transferable mechanism knowledge explicit instead of relying on the model to recover it from raw issue text.

## 4. Controlled result

The clean replication contains ten attempts per condition in `results/experiment2_replication2.csv`:

| Condition | Mechanism matches | Attempts | Verified F2P |
| --- | ---: | ---: | ---: |
| A — Target only | 0 | 10 | 0 |
| B — Raw history | 1 | 10 | 0 |
| C — Structured history | 6 | 10 | 0 |

Structured history improved mechanism targeting in this selected case. It did not by itself produce an executable differential test.

## 5. What improved

The cumulative record in `results/experiment2_re_evaluated.csv` contains 25 attempts per condition:

| Condition | Mechanism matches | Attempts | Verified F2P |
| --- | ---: | ---: | ---: |
| A — Target only | 0 | 25 | 0 |
| B — Raw history | 2 | 25 | 0 |
| C — Structured history | 15 | 25 | 2 |

The cumulative mechanism-match pattern supports the same narrow targeting conclusion. The two F2P cases occurred in exploratory structured-history runs and were verified against buggy and fixed revisions.

## 6. What did not improve

The clean replication produced zero F2P in all conditions. The two cumulative structured-history F2P results did not reproduce in the clean replication. Therefore, the evidence supports a mechanism-targeting improvement, not a stable F2P improvement claim.

## 7. Root-cause diagnosis

The remaining bottleneck was the transition from a correct mechanism hypothesis to a concrete precondition/state/action/observable/assertion. Correct hypotheses still produced weak triggers, wrong-shaped assertions, model-output failures, or mechanical setup failures.

## 8. Trigger Plan refinement

Experiment 4 addressed that downstream bottleneck with a strict Trigger Plan contract, deterministic validation, and bounded repair:

- valid plans improved from 2/5 hypotheses to 5/5;
- hypotheses with at least one F2P improved from 3/5 for direct generation to 4/5 for the planner under the budget-matched comparison;
- direct generation remained more efficient per generated test.

The Trigger Plan improved reliability and hypothesis coverage, but not per-test trigger efficiency. It is a follow-up implementation refinement, not the main contribution.

## 9. Current implementation status

The repository preserves the A/B/C evidence, leakage boundary, frozen hypotheses, generated tests, evaluator, execution logs, and Experiment 4 replay bundle. Deterministic verifiers now derive the core and downstream claims from machine-readable evidence. The current target and history selection remain deliberately narrow and retrospective.

## 10. Limitations

This is one selected target with small attempt counts, no statistical significance analysis, no recall denominator, and no broad cross-project generalization claim. A mechanism match is not equivalent to a verified F2P test.

## 11. Next engineering step

Keep the structured-history comparison and evaluator frozen while improving observable/assertion alignment and trigger-plan validity on a newly specified held-out set. Any future evaluation should separate retrieval quality, mechanism targeting, and executable test construction.
