# Artifact schema

All persisted domain artifacts use `schema_version: "1"`, a stable identifier,
and a `run_id`. JSON serialization is key-deterministic for hashing.

| Artifact | Important fields |
|---|---|
| `FrozenHypothesis` | hypothesis hash, oracle, visible input manifest, frozen marker |
| `TriggerPlan` | plan hash, prompt hash, strategy, ordered actions, observable, assertion |
| `TestArtifact` | test hash, prompt hash, prompt strategy, arm, plan id, visible manifest |
| `ExecutionResult` | command, runner result, exit code, normalized log, exception |
| `PairExecutionResult` | unchanged-test flag plus buggy/fixed results |
| `EvaluationResult` | classification, failure category, oracle support, evaluator version |
| `RunEvent` | stage, status, payload, timestamp, append-only event id |
| `RunSummary` | config hash, source commit, token totals, aggregate metrics |

Generation-visible manifests are stored with hypotheses and tests. Fixed
revision paths and evaluator truth are not included in generation prompts or
generation-visible model fields.
