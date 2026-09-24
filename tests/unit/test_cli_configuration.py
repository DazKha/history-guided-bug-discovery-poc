import json
from pathlib import Path

import pytest

from history_guided_bug_discovery.adapters.providers import create_provider
from history_guided_bug_discovery.config.loader import ConfigError, load_config


ROOT = Path(__file__).resolve().parents[2]


def test_config_resolves_target_checkout_from_repository_root(tmp_path):
    source = json.loads((ROOT / "configs/experiment4.json").read_text(encoding="utf-8"))
    source["target"]["buggy_checkout"] = "workspace/buggy"
    source["target"]["fixed_checkout"] = "workspace/fixed"
    config_path = tmp_path / "configs" / "run.json"
    config_path.parent.mkdir()
    config_path.write_text(json.dumps(source), encoding="utf-8")
    config = load_config(config_path)
    assert config.repository_root == tmp_path
    assert config.target["buggy_checkout"] == str((tmp_path / "workspace" / "buggy").resolve())
    assert config.target["fixed_checkout"] == str((tmp_path / "workspace" / "fixed").resolve())


def test_existing_relative_checkout_still_resolves_from_repository_root(tmp_path):
    source = json.loads((ROOT / "configs/experiment4.json").read_text(encoding="utf-8"))
    source["target"]["buggy_checkout"] = "workspace/buggy"
    source["target"]["fixed_checkout"] = "workspace/fixed"
    (tmp_path / "workspace/buggy").mkdir(parents=True)
    (tmp_path / "workspace/fixed").mkdir(parents=True)
    config_path = tmp_path / "configs" / "run.json"
    config_path.parent.mkdir()
    config_path.write_text(json.dumps(source), encoding="utf-8")

    config = load_config(config_path)

    assert config.target["buggy_checkout"] == str((tmp_path / "workspace/buggy").resolve())
    assert config.target["fixed_checkout"] == str((tmp_path / "workspace/fixed").resolve())


def test_config_path_resolution_does_not_depend_on_existence_or_cwd(tmp_path, monkeypatch):
    source = json.loads((ROOT / "configs/experiment4.json").read_text(encoding="utf-8"))
    source["target_context"] = "workspace/context.txt"
    source["structured_history"] = "workspace/history.json"
    source["frozen_hypotheses"] = "workspace/hypotheses.json"
    source["artifact_root"] = "workspace/artifacts"
    source["target_manifest"] = "workspace/manifest.json"
    source["target"]["buggy_checkout"] = "workspace/buggy"
    source["target"]["fixed_checkout"] = "workspace/fixed"
    absolute = tmp_path / "absolute-checkout"
    source["target"]["source_path_markers"] = ["src"]
    source["target"]["buggy_checkout"] = str(absolute)
    config_path = tmp_path / "configs" / "run.json"
    config_path.parent.mkdir()
    config_path.write_text(json.dumps(source), encoding="utf-8")

    monkeypatch.chdir(tmp_path / "configs")
    config = load_config(config_path, tmp_path)

    assert config.paths.target_context == (tmp_path / "workspace/context.txt").resolve()
    assert config.paths.structured_history == (tmp_path / "workspace/history.json").resolve()
    assert config.paths.frozen_hypotheses == (tmp_path / "workspace/hypotheses.json").resolve()
    assert config.paths.artifact_root == (tmp_path / "workspace/artifacts").resolve()
    assert config.paths.target_manifest == (tmp_path / "workspace/manifest.json").resolve()
    assert config.target["buggy_checkout"] == absolute.resolve().as_posix()
    assert config.target["fixed_checkout"] == (tmp_path / "workspace/fixed").resolve().as_posix()


def test_unsupported_provider_fails_before_provider_construction(tmp_path):
    source = json.loads((ROOT / "configs/experiment4.json").read_text(encoding="utf-8"))
    source["model"]["provider"] = "unsupported"
    config_path = tmp_path / "run.json"
    config_path.write_text(json.dumps(source), encoding="utf-8")
    config = load_config(config_path, ROOT)
    with pytest.raises(ConfigError, match="unsupported model.provider"):
        create_provider(config)
