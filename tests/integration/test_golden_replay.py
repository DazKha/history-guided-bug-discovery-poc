from pathlib import Path

from history_guided_bug_discovery.application.replay_pipeline import ReplayPipeline
from history_guided_bug_discovery.config.loader import load_config
from history_guided_bug_discovery.domain.enums import Arm


ROOT = Path(__file__).resolve().parents[2]


def test_experiment4_c2_golden_replay_matches_preserved_baseline_without_api_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    config = load_config(ROOT / "configs/experiment4.json", ROOT)
    summary = ReplayPipeline().replay(config, ROOT / "artifacts/experiment4/iteration3", Arm.STRICT_PLANNER)
    assert summary.candidate_slots == 15
    assert summary.generated_test_artifacts == 13
    assert summary.f2p == 5
    assert summary.f2p_hypotheses == 4
    assert summary.p2p == 3
    assert summary.mechanical_failures == 5
    assert summary.model_output_failures == 2
    assert summary.f2f == 0
    assert summary.llm_calls == 21
    assert summary.total_tokens == 326930


def test_experiment4_budgeted_direct_golden_replay_matches_preserved_baseline():
    config = load_config(ROOT / "configs/experiment4.json", ROOT)
    summary = ReplayPipeline().replay(config, ROOT / "artifacts/experiment4/iteration3", Arm.BUDGET_MATCHED_DIRECT)
    assert summary.candidate_slots == 15
    assert summary.generated_test_artifacts == 13
    assert summary.f2p == 6
    assert summary.f2p_hypotheses == 3
    assert summary.f2f == 2
    assert summary.p2p == 5
    assert summary.model_output_failures == 2
    assert summary.llm_calls == 15
    assert summary.total_tokens == 15801
