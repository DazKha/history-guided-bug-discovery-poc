from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config.models import RunConfig
from ..domain.enums import Arm
from ..reporting.aggregate import AggregateSummary, aggregate_rows, validate_consistency


EVIDENCE_SCHEMA_VERSION = "experiment4-evidence-v1"


class EvidenceBundleError(ValueError):
    """Raised when a supplied evidence bundle is absent, corrupt, or inconsistent."""


@dataclass(frozen=True)
class LoadedEvidenceBundle:
    manifest: dict[str, Any]
    rows: tuple[dict[str, str], ...]
    summary: AggregateSummary


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _same_root(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _metric_view(summary: AggregateSummary) -> dict[str, Any]:
    values = summary.to_dict()
    values.pop("metadata", None)
    return values


def load_evidence_bundle(artifacts: str | Path, arm: Arm, config: RunConfig | None = None) -> LoadedEvidenceBundle:
    """Load and validate one self-contained arm bundle beneath ``artifacts``."""

    root = Path(artifacts).resolve()
    if not root.is_dir():
        raise EvidenceBundleError(f"evidence bundle root does not exist: {root}")
    bundle_dir = (root / arm.value).resolve()
    if not _same_root(bundle_dir, root) or not bundle_dir.is_dir():
        raise EvidenceBundleError(f"evidence bundle for arm {arm.value} is missing: {bundle_dir}")
    manifest_path = bundle_dir / "evidence-bundle.json"
    if not manifest_path.is_file():
        raise EvidenceBundleError(f"evidence bundle manifest is missing: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceBundleError(f"cannot read evidence bundle manifest {manifest_path}: {exc}") from exc
    if not isinstance(manifest, dict):
        raise EvidenceBundleError("evidence bundle manifest must be a JSON object")
    required = {
        "schema_version", "experiment_id", "run_id", "arm", "authoritative_row_source",
        "evidence_row_source", "authoritative_source_sha256", "evidence_sha256",
        "expected_hypothesis_count", "candidate_count", "evaluator_version",
        "expected_aggregate_metrics", "provenance",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise EvidenceBundleError("evidence bundle manifest missing field(s): " + ", ".join(missing))
    if manifest["schema_version"] != EVIDENCE_SCHEMA_VERSION:
        raise EvidenceBundleError(f"unsupported evidence bundle schema: {manifest['schema_version']}")
    if manifest["arm"] != arm.value:
        raise EvidenceBundleError(f"evidence bundle arm mismatch: {manifest['arm']!r} != {arm.value!r}")
    evidence_path = (bundle_dir / str(manifest["evidence_row_source"])).resolve()
    if not _same_root(evidence_path, bundle_dir) or not evidence_path.is_file():
        raise EvidenceBundleError(f"evidence row source is missing or escapes bundle: {evidence_path}")
    actual_hash = _sha256(evidence_path)
    if actual_hash != manifest["evidence_sha256"]:
        raise EvidenceBundleError(f"evidence hash mismatch for {evidence_path}: {actual_hash} != {manifest['evidence_sha256']}")
    if config is not None and manifest["evaluator_version"] != config.evaluator.version:
        raise EvidenceBundleError("evaluator version mismatch between config and evidence bundle")
    try:
        with evidence_path.open(newline="", encoding="utf-8") as handle:
            rows = tuple(csv.DictReader(handle))
    except (OSError, csv.Error) as exc:
        raise EvidenceBundleError(f"cannot read evidence rows {evidence_path}: {exc}") from exc
    if not rows:
        raise EvidenceBundleError(f"evidence rows are empty: {evidence_path}")
    if any(row.get("arm") != arm.value for row in rows):
        raise EvidenceBundleError("evidence rows contain a different arm")
    summary = aggregate_rows(list(rows), arm)
    try:
        validate_consistency(summary)
    except ValueError as exc:
        raise EvidenceBundleError(f"evidence aggregate is inconsistent: {exc}") from exc
    if summary.candidate_slots != int(manifest["candidate_count"]):
        raise EvidenceBundleError("evidence candidate count disagrees with manifest")
    if summary.total_hypotheses != int(manifest["expected_hypothesis_count"]):
        raise EvidenceBundleError("evidence hypothesis count disagrees with manifest")
    expected = manifest["expected_aggregate_metrics"]
    if not isinstance(expected, dict) or _metric_view(summary) != expected:
        raise EvidenceBundleError("evidence aggregate disagrees with manifest")
    return LoadedEvidenceBundle(manifest, rows, summary)


def write_evidence_bundle(
    artifact_root: str | Path,
    arm: Arm,
    rows: list[dict[str, Any]],
    authoritative_source: str,
    authoritative_source_sha256: str,
    evaluator_version: str,
    provenance: dict[str, Any],
) -> Path:
    """Write a deterministic immutable bundle from already-authoritative rows."""

    from ..reporting.aggregate import aggregate_rows

    bundle_dir = Path(artifact_root) / arm.value
    bundle_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = bundle_dir / "evidence-rows.csv"
    if not rows:
        raise ValueError("cannot write an empty evidence bundle")
    fieldnames = list(rows[0])
    with evidence_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    summary = aggregate_rows(rows, arm)
    validate_consistency(summary)
    manifest = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "experiment_id": "experiment4",
        "run_id": "experiment4-final-iteration3",
        "arm": arm.value,
        "authoritative_row_source": authoritative_source,
        "evidence_row_source": evidence_path.name,
        "authoritative_source_sha256": authoritative_source_sha256,
        "evidence_sha256": _sha256(evidence_path),
        "expected_hypothesis_count": summary.total_hypotheses,
        "candidate_count": summary.candidate_slots,
        "evaluator_version": evaluator_version,
        "expected_aggregate_metrics": _metric_view(summary),
        "provenance": provenance,
    }
    manifest_path = bundle_dir / "evidence-bundle.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_path
