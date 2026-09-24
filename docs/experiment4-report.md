# Experiment 4 report

Experiment 4 is a downstream engineering refinement to the executable-test
generation stage. It does not replace the structured-history mechanism-targeting
result described in [`docs/engineering-results.md`](engineering-results.md).

## Evidence

The final strict planner arm (C2) retained five frozen hypotheses and allocated
15 candidate slots. It produced 13 generated/executed test artifacts: five F2P,
three P2P, five mechanical failures, two model-output failures, and zero final
F2F. Four of five hypotheses had at least one F2P. The run used 21 LLM calls and
326,930 recorded tokens; five of six planner attempts were valid immediately and
the one rejected response was repaired.

The budget-matched direct arm used the same 15 slots and produced 13 generated
tests: six F2P across three hypotheses, two F2F, five P2P, and two model-output
failures. It used 15 calls and 15,801 tokens.

## Interpretation

The strict Trigger Plan contract improved valid plans from 2/5 hypotheses to
5/5 after deterministic validation and bounded repair. Under the
budget-matched comparison, it improved hypothesis-level F2P coverage from 3/5
for direct generation to 4/5 for the planner. Candidate-level F2P efficiency
did not improve: C2 produced 5/15 F2P versus 6/15 for direct generation. The
correct conclusion is that the planner improved reliability and hypothesis
coverage, but not per-test trigger efficiency. This is directional evidence
from one selected target, not an architecture proof or cross-project
generalization claim.

## Reproduction

Run the offline golden replay and report commands in
[`reproducibility.md`](reproducibility.md). The authoritative rows remain in
`results/experiment4_iteration3_raw.csv` and
`results/experiment4_iteration3_raw_budgeted.csv`.

The evidence boundary is narrow: this is a deterministic replay of one
target-specific preserved run, not a new discovery execution, statistical
significance claim, or cross-project generalization result. The conclusion
remains CASE B / mixed: strict planning improves planner validity and
hypothesis-level coverage, while direct generation remains more efficient per
candidate.
