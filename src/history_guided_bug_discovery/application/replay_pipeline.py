from __future__ import annotations

from pathlib import Path

from ..config.models import RunConfig
from ..domain.enums import Arm
from .evidence_bundle import load_evidence_bundle
from ..reporting.aggregate import AggregateSummary


class ReplayPipeline:
    """Offline replay over preserved Experiment 4 machine-readable rows."""

    def replay(self, config: RunConfig, artifacts: str | Path, arm: Arm = Arm.STRICT_PLANNER) -> AggregateSummary:
        artifact_path = Path(artifacts)
        if not artifact_path.is_absolute():
            artifact_path = config.repository_root / artifact_path
        return load_evidence_bundle(artifact_path, arm, config).summary
