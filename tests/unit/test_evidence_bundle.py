import csv
import json
import shutil
from pathlib import Path

import pytest

from history_guided_bug_discovery.application.evidence_bundle import EvidenceBundleError, load_evidence_bundle
from history_guided_bug_discovery.application.replay_pipeline import ReplayPipeline
from history_guided_bug_discovery.config.loader import load_config
from history_guided_bug_discovery.domain.enums import Arm


ROOT = Path(__file__).resolve().parents[2]


def _copy_bundle(tmp_path: Path, arm: str = "C2") -> Path:
    source = ROOT / "artifacts" / "experiment4" / "iteration3"
    target = tmp_path / "bundle"
    shutil.copytree(source, target)
    return target


def test_replay_requires_manifest_inside_supplied_bundle(tmp_path):
    bundle = _copy_bundle(tmp_path)
    (bundle / "C2" / "evidence-bundle.json").unlink()
    config = load_config(ROOT / "configs/experiment4.json", ROOT)

    with pytest.raises(EvidenceBundleError, match="manifest"):
        ReplayPipeline().replay(config, bundle, Arm.STRICT_PLANNER)


def test_replay_rejects_corrupt_evidence_file(tmp_path):
    bundle = _copy_bundle(tmp_path)
    evidence = bundle / "C2" / "evidence-rows.csv"
    evidence.write_text(evidence.read_text(encoding="utf-8") + "corruption\n", encoding="utf-8")
    config = load_config(ROOT / "configs/experiment4.json", ROOT)

    with pytest.raises(EvidenceBundleError, match="hash"):
        ReplayPipeline().replay(config, bundle, Arm.STRICT_PLANNER)


def test_replay_rejects_manifest_hash_mismatch(tmp_path):
    bundle = _copy_bundle(tmp_path)
    manifest_path = bundle / "C2" / "evidence-bundle.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["evidence_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    config = load_config(ROOT / "configs/experiment4.json", ROOT)

    with pytest.raises(EvidenceBundleError, match="hash"):
        ReplayPipeline().replay(config, bundle, Arm.STRICT_PLANNER)


def test_replay_rejects_aggregate_mismatch(tmp_path):
    bundle = _copy_bundle(tmp_path)
    manifest_path = bundle / "C2" / "evidence-bundle.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["expected_aggregate_metrics"]["f2p"] = 999
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    config = load_config(ROOT / "configs/experiment4.json", ROOT)

    with pytest.raises(EvidenceBundleError, match="aggregate"):
        ReplayPipeline().replay(config, bundle, Arm.STRICT_PLANNER)


def test_bundle_loader_does_not_read_repository_results(tmp_path):
    bundle = _copy_bundle(tmp_path)
    manifest_path = bundle / "C2" / "evidence-bundle.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["authoritative_row_source"] = "../../../../outside/results.csv"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = load_evidence_bundle(bundle, Arm.STRICT_PLANNER)
    assert result.summary.f2p == 5
