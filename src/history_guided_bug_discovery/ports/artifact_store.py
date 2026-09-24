from pathlib import Path
from typing import Protocol

from ..domain.models import RunEvent


class SerializableArtifact(Protocol):
    @property
    def stable_id(self) -> str:
        ...

    def to_dict(self) -> dict:
        ...


class ArtifactStore(Protocol):
    def append_event(self, event: RunEvent) -> None:
        ...

    def save_artifact(self, artifact: SerializableArtifact) -> Path:
        ...

    def load_run(self, run_id: str) -> list[RunEvent]:
        ...

    def load_artifact_records(self, run_id: str) -> list[dict]:
        ...
