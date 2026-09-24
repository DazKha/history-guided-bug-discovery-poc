import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from history_guided_bug_discovery.config.loader import ConfigError, load_config
from history_guided_bug_discovery.domain.enums import Arm, PairClassification, Stage
from history_guided_bug_discovery.domain.models import FrozenHypothesis, TestArtifact as DomainTestArtifact, stable_hash


def test_domain_serialization_is_deterministic_and_versioned():
    hypothesis = FrozenHypothesis.from_record(
        run_id="run-1",
        hypothesis_id="h1",
        record={"hypothesis": "claim", "trigger": "trigger", "oracle": {"expected_behavior": "pass"}},
        generation_visible_files=("data/context.txt",),
    )
    first = hypothesis.to_dict()
    second = json.loads(json.dumps(first, sort_keys=True))
    assert first == second
    assert first["schema_version"] == "1"
    assert first["hypothesis_sha256"] == stable_hash({"hypothesis": "claim", "trigger": "trigger", "potential_failure": "", "oracle": {"expected_behavior": "pass"}})


def test_frozen_hypothesis_rejects_mutation_and_round_trips_enum():
    hypothesis = FrozenHypothesis.from_record("run-1", "h1", {"hypothesis": "claim", "oracle": {"nested": {"value": 1}}}, ())
    with pytest.raises(FrozenInstanceError):
        hypothesis.claim = "changed"
    with pytest.raises(TypeError):
        hypothesis.oracle["nested"] = {}
    assert Arm.STRICT_PLANNER.value == "C2"
    assert PairClassification.F2P.value == "F2P"
    assert Stage.EVALUATE.value == "EVALUATE"


def test_test_artifact_hash_is_stable():
    artifact = DomainTestArtifact.create(
        run_id="run-1", artifact_id="t1", hypothesis_id="h1", arm=Arm.DIRECT,
        code="def test_value():\n    assert 1 == 1\n", prompt_hash="p1",
        generation_visible_manifest=("data/context.txt",),
    )
    assert artifact.test_sha256 == stable_hash(artifact.code)
    assert DomainTestArtifact.from_dict(artifact.to_dict()) == artifact


def test_config_loader_resolves_paths_and_hashes_config():
    config = load_config(Path("configs/experiment4.json"), repository_root=Path.cwd())
    assert config.run_id == "experiment4-final"
    assert config.target_id == "PySnooper:1"
    assert config.paths.target_context.is_absolute()
    assert config.config_hash
    assert config.planner.candidate_count == 3


def test_config_loader_rejects_unknown_fields_and_invalid_timeout(tmp_path):
    source = json.loads(Path("configs/experiment4.json").read_text())
    source["unknown"] = True
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(source))
    with pytest.raises(ConfigError, match="unknown"):
        load_config(path, repository_root=tmp_path)

    source = json.loads(Path("configs/experiment4.json").read_text())
    source["execution"]["timeout_seconds"] = 0
    path.write_text(json.dumps(source))
    with pytest.raises(ConfigError, match="timeout"):
        load_config(path, repository_root=tmp_path)

    source = json.loads(Path("configs/experiment4.json").read_text())
    source["planner"]["candidate_count"] = 0
    path.write_text(json.dumps(source))
    with pytest.raises(ConfigError, match="candidate_count"):
        load_config(path, repository_root=tmp_path)

    source = json.loads(Path("configs/experiment4.json").read_text())
    del source["model"]["name"]
    path.write_text(json.dumps(source))
    with pytest.raises(ConfigError, match="model.name"):
        load_config(path, repository_root=tmp_path)
