"""Compatibility exports for the strict Experiment 4 trigger-plan contract."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from history_guided_bug_discovery.application.planning_service import (  # noqa: F401
    ACTION_FIELDS, ACTION_TYPES, ASSERTION_FIELDS, OBSERVABLE_FIELDS, PLAN_FIELDS,
    parse_plan_response, validate_trigger_plan,
)

validate_plan = validate_trigger_plan
