# Experiment 4 Engineering Hardening Design

## Goal

Make the preserved Experiment 4 system installable, artifact-driven, resumable,
configuration-rooted, and safe to execute without changing evaluator semantics
or any frozen result.

## Design

Each preserved arm receives an immutable evidence bundle under
`artifacts/experiment4/iteration3/<arm>/`. Its manifest records the bundle
schema, arm, source provenance, hashes, evaluator version, expected dimensions,
and the complete aggregate. Replay reads only the manifest and its co-located
row snapshot, validates both hashes and aggregate metrics, and never discovers
files through parent directories or constructs an LLM provider.

The discovery ledger remains append-only. Resume indexes existing events and
immutable artifacts by `(hypothesis_id, candidate_id)`, validates artifact
hashes, and runs only the first incomplete stage. It reconstructs a summary
from the complete ledger and refuses to report completion while required
candidate stages remain unfinished.

CLI configuration is resolved from the config/repository root. A provider
registry accepts only configured providers and fails unsupported values before
starting a run. The subprocess executor writes a unique sanitized file inside
the checkout, records the exact content hash through the artifact, avoids a
shell, and removes the file on every exit path.

Packaging uses `pyproject.toml` with `src/` discovery, runtime `requests`, a
pytest development extra, and four console scripts. CI runs compilation,
tests, offline replays, and the deterministic artifact verifier on Python 3.11
and 3.12 without an API key or external benchmark checkout.

## Verification

Tests cover bundle corruption and mismatch, replay without credentials,
stage-aware resume after each major crash point, provider selection and
external-CWD paths, executor cleanup/error cases, exact frozen metrics, report
consistency, and the absence of public Experiment 4-excluded material.
