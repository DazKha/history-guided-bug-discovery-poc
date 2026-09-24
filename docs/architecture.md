# Architecture

```mermaid
flowchart LR
  C[Versioned RunConfig] --> P[DiscoveryPipeline]
  H[Frozen hypotheses + structured history] --> P
  P --> S[Application services]
  S --> L[LLMProvider port]
  S --> T[TargetAdapter port]
  T --> E[TestExecutor port]
  E --> B[BenchmarkEvaluator]
  S --> A[ArtifactStore JSONL]
  B --> A
  A --> R[Replay + reporting]
```

## Boundaries

- Domain models are immutable where they represent evidence and carry schema
  versions, stable identifiers, provenance, and hashes.
- Prompt builders expose explicit strategies: `direct_test_v1`,
  `strict_trigger_plan_v1`, and `plan_to_test_compact_v1`.
- The target adapter owns checkout paths, interpreter selection, runner choice,
  environment, and source-path markers.
- The executor owns subprocess lifecycle, normalized logs, timeouts, exit codes,
  and cleanup of injected tests.
- `BenchmarkEvaluator` owns the preserved buggy/fixed revision semantics. The
  discovery pipeline can instead use `FindingValidator` when no fixed revision
  exists.
- The artifact store is append-only and refuses duplicate events or writes after
  a completed run.

## Stage flow

`LOAD_CONFIG → PREPARE_TARGET → LOAD_HISTORY → LOAD_OR_GENERATE_HYPOTHESIS →
FREEZE_HYPOTHESIS → GENERATE_TRIGGER_PLAN → VALIDATE_TRIGGER_PLAN →
GENERATE_TEST → PREFLIGHT_TEST → EXECUTE_BUGGY → EXECUTE_FIXED → EVALUATE →
PERSIST → REPORT`

Resume mode uses the ledger to skip already completed candidate-generation
stages; a completed run is never silently overwritten.
