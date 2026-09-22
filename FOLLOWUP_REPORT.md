# Follow-up report

After the presentation feedback, I tested one uncertain assumption from the proposal: whether structured, applicability-aware historical bug knowledge would produce more verifiable proactive discoveries than target-only exploration or raw historical RAG.

I ran a controlled nine-attempt study on a real BugsInPy target (`PySnooper:1`) with six historical bugs from two projects. All conditions used the same DeepSeek model, target context, attempt count, output budget, repair budget, and runtime. B and C received the same historical IDs; C received structured, evidence-bearing units and was allowed to return `NO_SUPPORTED_HYPOTHESIS`.

The target harness itself worked: the unchanged benchmark regression failed on the buggy revision and passed on the fixed revision. The generated-test comparison produced zero F2P discoveries in every condition. Target-only generated four tests (three P2P and one mechanical) and abstained once; raw history generated none; structured history generated none and returned `NO_SUPPORTED_HYPOTHESIS` in all five attempts.

The honest conclusion is feasibility of the evaluation harness, not proof that the proposed architecture works. This run does not show a discovery advantage for structured history. It does show a useful conservative behavior: C did not turn historical invariants into unsupported target oracles. A larger follow-up should use more held-out targets, pre-registered retrieval, and enough attempts to distinguish abstention quality from lack of generation.

Limitations: one target, five attempts per condition, retrospective history selection, and no statistical inference or recall estimate.
