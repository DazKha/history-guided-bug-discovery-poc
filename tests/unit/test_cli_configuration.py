import json
from pathlib import Path

import pytest

from history_guided_bug_discovery.adapters.providers import create_provider
from history_guided_bug_discovery.config.loader import ConfigError, load_config


ROOT = Path(__file__).resolve().parents[2]


def test_config_resolves_target_checkout_from_config_root(tmp_path):
    source = json.loads((ROOT / "configs/experiment4.json").read_text(encoding="utf-8"))
    source["target"]["buggy_checkout"] = "workspace/buggy"
    source["target"]["fixed_checkout"] = "workspace/fixed"
    config_path = tmp_path / "configs" / "run.json"
    config_path.parent.mkdir()
    config_path.write_text(json.dumps(source), encoding="utf-8")
    config = load_config(config_path)
    assert config.repository_root == tmp_path
    assert config.target["buggy_checkout"] == str((tmp_path / "configs" / "workspace" / "buggy").resolve())


def test_unsupported_provider_fails_before_provider_construction(tmp_path):
    source = json.loads((ROOT / "configs/experiment4.json").read_text(encoding="utf-8"))
    source["model"]["provider"] = "unsupported"
    config_path = tmp_path / "run.json"
    config_path.write_text(json.dumps(source), encoding="utf-8")
    config = load_config(config_path, ROOT)
    with pytest.raises(ConfigError, match="unsupported model.provider"):
        create_provider(config)
