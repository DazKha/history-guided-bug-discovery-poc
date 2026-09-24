from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..config.models import RunConfig
from ..domain.models import FrozenHypothesis, HistoricalBugUnit, TargetContext


class HypothesisService:
    def load_context(self, config: RunConfig) -> TargetContext:
        return TargetContext.create(config.run_id, config.target_id, config.paths.target_context.read_text(encoding="utf-8"), config.generation_visible_manifest)

    def load_history(self, config: RunConfig) -> tuple[HistoricalBugUnit, ...]:
        value = json.loads(config.paths.structured_history.read_text(encoding="utf-8"))
        records = value if isinstance(value, list) else [value]
        result = []
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                record = {"value": record}
            history_id = str(record.get("history_id") or record.get("bug_id") or record.get("id") or f"history-{index + 1}")
            summary = str(record.get("summary") or record.get("context") or record.get("observed_failure") or "")
            mechanism = str(record.get("mechanism") or record.get("failure_mechanism") or record.get("failure_pattern") or "")
            result.append(HistoricalBugUnit(config.run_id, history_id, summary, mechanism, record))
        return tuple(result)

    def load_frozen(self, config: RunConfig) -> list[FrozenHypothesis]:
        raw = json.loads(config.paths.frozen_hypotheses.read_text(encoding="utf-8"))
        records = raw if isinstance(raw, list) else raw.get("hypotheses", [])
        visible = config.generation_visible_manifest
        result = []
        for index, record in enumerate(records[:5], 1):
            provisional = FrozenHypothesis.from_record(config.run_id, f"conditional-h{index:02d}", record, visible)
            hypothesis_id = f"conditional-h{index:02d}-{provisional.hypothesis_sha256[:10]}"
            result.append(FrozenHypothesis.from_record(config.run_id, hypothesis_id, record, visible))
        return result
