# Experiment 3 failure analysis

## 3A natural stage

Five fresh hypothesis calls produced 3 `NO_SUPPORTED_HYPOTHESIS` and 2 model-output errors. No tests were generated, so no trigger-level semantic classification is possible for 3A.

## 3B conditional stage

| Arm | Hypotheses | Tests | Classification counts | Main failure |
|---|---:|---:|---|---|
| C1 direct | 5 | 5 | 2 ASSERTION_F2P, 1 F2F, 2 P2P | direct trigger instability |
| C2 planner | 5 | 8 | 3 ASSERTION_F2P, 3 F2F, 2 P2P | 3 hypotheses never yielded valid planner output |

C2 had 12 planner attempts across the initial call and two bounded repairs: 5 initial, 4 first repairs, and 3 second repairs. Two hypotheses eventually yielded four triggers each. Three hypotheses remained non-executable at the planner stage; these were retained in accounting and not silently dropped.

For executable C2 tests, six of eight reached a meaningful buggy failure. The three F2F cases show that a trigger can reach target behavior while the observable/assertion still fails on both revisions. The two P2P cases show the remaining trigger-too-weak path. No evaluator thresholds, oracle rules, or fixed-revision information were changed.
