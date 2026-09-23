from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


def expand_trigger_rows(hypothesis: dict[str, Any], trigger_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for trigger in trigger_rows:
        row = dict(hypothesis)
        row.update(trigger)
        rows.append(row)
    return rows


def summarize_trigger_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row.get("mode", "")), str(row.get("arm", "")))].append(row)
    summary = []
    for (mode, arm), subset in sorted(groups.items()):
        hypotheses = {row.get("hypothesis_id") for row in subset if row.get("hypothesis_id")}
        f2p = sum(bool(row.get("verified_f2p")) for row in subset)
        executable = sum(row.get("test_status") == "EXECUTABLE" for row in subset)
        activated = sum(row.get("activation") == "ACTIVATED" for row in subset)
        summary.append({
            "mode": mode,
            "arm": arm,
            "hypotheses": len(hypotheses),
            "generated_triggers": len(subset),
            "executable_triggers": executable,
            "trigger_executability_rate": executable / len(subset) if subset else 0.0,
            "activated_triggers": activated,
            "trigger_activation_rate": activated / executable if executable else 0.0,
            "verified_f2p": f2p,
            "f2p_per_hypothesis": f2p / len(hypotheses) if hypotheses else 0.0,
            "f2p_per_executed_trigger": f2p / executable if executable else 0.0,
            "unique_failure_modes": len({row.get("classification") for row in subset if row.get("classification")}),
            "executions_per_verified_f2p": executable / f2p if f2p else "INF",
        })
    return summary

