# Experiment 5 failure analysis

## Target and harness

The independent Tornado reproducer gave exit `1` on the buggy checkout and exit `0` on the fixed checkout. The buggy log contains the target-side assertion in `WebSocketHandler.set_nodelay` and the missing WebSocket message; the fixed log is `OK`. No evaluator or leakage defect was found.

## End-to-end taxonomy

| Condition | Failure category | Count | Diagnosis |
|---|---|---:|---|
| A | ORACLE_UNSUPPORTED | 3 | Generated hypotheses lacked target-supported pre-execution oracle evidence; they were not used as semantic successes. |
| A | SEMANTIC_NON_TRIGGER | 7 | Six tests were P2P and one was F2F; all concerned unrelated demo/HTML escaping behavior rather than the selected WebSocket mechanism. |
| B | MODEL_OUTPUT_FAILURE | 3 | One malformed/non-JSON model response and two explicit `NO_SUPPORTED_HYPOTHESIS` responses. |
| B | ORACLE_UNSUPPORTED | 3 | Raw-history hypotheses targeted demo modules or otherwise lacked a supported target oracle. |
| B | SEMANTIC_NON_TRIGGER | 4 | Three P2P tests and one F2F test; generated hypotheses focused on unrelated demo or encoding behavior. Three of these also had import/setup failures in raw execution logs. |
| C | ORACLE_UNSUPPORTED | 1 | One generated hypothesis had no supported target-side oracle. |
| C | SEMANTIC_NON_TRIGGER | 8 | Eight P2P tests targeted template/JSON/locale behavior rather than the WebSocket lifecycle mismatch. |
| C | MECHANICAL_FAILURE | 1 | The generated code attempted to execute `python -m unittest` as a filename on both revisions. |

## Mechanism-transfer diagnosis

There were no mechanism-matched hypotheses, so no mechanism-matched trigger could be assessed. The dominant failure occurred before trigger construction: history-guided generation did not identify the target mechanism. The structured condition was executable more often than raw history (10/10 versus 7/10), but this did not translate into target mechanism alignment or F2P.

The observed wrong mechanisms were:

- A: `tornado.escape.xhtml_escape` quote behavior and demo handlers.
- B: demo S3/chat paths plus encoding-related `tornado.escape` behavior.
- C: locale/encoding behavior in template loading and `json_decode`.

These are not hidden-target facts fed back to generation; they are post-execution classifications of preserved artifacts and logs.

## Conditional experiment

The conditional stage has no failure rows because it was stopped before generation under the explicit underpowered rule. Treating zero selected hypotheses as planner evidence would confound planner quality with failure to identify a mechanism, so it is reported as not estimable.
