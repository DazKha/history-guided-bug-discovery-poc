# Recommendations for the next experiment

These are not applied to the frozen replication protocol.

1. Separate mechanism hypothesis generation from trigger construction. Preserve the first supported mechanism hypothesis, then ask for one or more independently generated concrete triggers under the same budget.
2. Add explicit adversarial environment construction as a bounded test strategy: locale, encoding, filesystem, platform, or concurrency preconditions should be represented as executable setup only when supported by target evidence.
3. Diversify triggers for one supported mechanism rather than repeatedly regenerating unrelated hypotheses. This directly targets the observed mechanism-to-F2P conversion bottleneck.
4. Keep the exception-aware evaluator, but require generated tests to state whether the expected failure is an assertion or a target exception and to identify the expected target stack region.
5. Replicate across additional held-out targets before making any general claim. Keep retrospective transfer selection clearly separated from any future autonomous-retrieval evaluation.
6. Consider a preregistered C1/C2 ablation only after another frozen A/B/C replication: structured history without applicability versus structured history with applicability, with identical history and target context.
