import json
from dataclasses import replace
from pathlib import Path

from history_guided_bug_discovery.adapters.benchmark_evaluator import BenchmarkEvaluator
from history_guided_bug_discovery.adapters.bugsinpy import BugsInPyTargetAdapter
from history_guided_bug_discovery.adapters.json_artifact_store import JsonArtifactStore
from history_guided_bug_discovery.adapters.subprocess_executor import SubprocessExecutor
from history_guided_bug_discovery.application.discovery_pipeline import DiscoveryPipeline
from history_guided_bug_discovery.config.loader import load_config
from history_guided_bug_discovery.domain.enums import Arm, Stage
from history_guided_bug_discovery.ports.llm import GenerationResponse


class FakeProvider:
    def __init__(self):
        self.calls = 0

    def generate(self, request):
        self.calls += 1
        return GenerationResponse(json.dumps({"status": "TEST", "test_code": "def test_generated():\n    observed = 1\n    assert observed == 1\n"}), {"prompt_tokens": 1, "completion_tokens": 1}, self.calls, {"model": request.model})


def test_pipeline_records_typed_stages_and_uses_fake_provider(tmp_path):
    root = Path(__file__).resolve().parents[2]
    config = load_config(root / "configs/experiment4.json", root)
    target = tmp_path / "target"
    target.mkdir()
    local_paths = replace(config.paths, artifact_root=tmp_path / "artifacts")
    local_config = replace(config, run_id="pipeline-test", paths=local_paths, target={"buggy_checkout": str(target), "fixed_checkout": str(target), "python": "python3", "runner": "pytest", "source_path_markers": []})
    provider = FakeProvider()
    store = JsonArtifactStore(local_paths.artifact_root)
    adapter = BugsInPyTargetAdapter(local_config.paths.target_context, local_config.generation_visible_manifest, "python3", "pytest")
    summary = DiscoveryPipeline(local_config, provider, SubprocessExecutor(), BenchmarkEvaluator(()), store, adapter).run(Arm.DIRECT)
    stages = [event.stage for event in store.load_run("pipeline-test")]
    assert Stage.LOAD_CONFIG in stages
    assert Stage.FREEZE_HYPOTHESIS in stages
    assert Stage.GENERATE_TEST in stages
    assert Stage.PERSIST in stages
    assert Stage.REPORT in stages
    assert provider.calls == 5
    assert summary.metrics["hypotheses"] == 5
