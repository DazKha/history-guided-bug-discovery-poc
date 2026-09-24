# Artifact schema

All persisted domain artifacts use `schema_version: "1"`, a stable identifier,
and a `run_id`. JSON serialization is key-deterministic for hashing.

The preserved offline evidence uses `schema_version:
"experiment4-evidence-v1"` in one manifest per arm. Each manifest is beside
its `evidence-rows.csv` and declares the experiment/run identifier, arm,
authoritative row source and SHA-256, snapshot SHA-256, expected hypothesis and
candidate counts, evaluator version, provenance, and the expected aggregate
metrics. Replay rejects a missing manifest, an escaping row source, a hash
mismatch, or an aggregate mismatch.

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
