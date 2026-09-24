from __future__ import annotations

import json
from pathlib import Path

from ..domain.models import RunEvent
from ..domain.enums import Stage


class JsonArtifactStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _run_root(self, run_id: str) -> Path:
        path = self.root / run_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _events_path(self, run_id: str) -> Path:
        return self._run_root(run_id) / "events.jsonl"

    def append_event(self, event: RunEvent) -> None:
        path = self._events_path(event.run_id)
        existing = self.load_run(event.run_id)
        if any(item.event_id == event.event_id for item in existing):
            raise ValueError(f"duplicate event: {event.event_id}")
        if any(item.stage is Stage.REPORT and item.status == "COMPLETE" for item in existing):
            raise ValueError(f"run {event.run_id} is completed")
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")

    def save_artifact(self, artifact) -> Path:
        run_root = self._run_root(artifact.to_dict()["run_id"])
        events = self.load_run(artifact.to_dict()["run_id"])
        if any(item.stage is Stage.REPORT and item.status == "COMPLETE" for item in events):
            raise ValueError(f"run {artifact.to_dict()['run_id']} is completed")
        path = run_root / "artifacts" / f"{artifact.stable_id.replace(':', '__')}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(artifact.to_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        if path.exists():
            if path.read_text(encoding="utf-8") != payload:
                raise ValueError(f"artifact overwrite refused: {path}")
            return path
        path.write_text(payload, encoding="utf-8")
        return path

    def load_run(self, run_id: str) -> list[RunEvent]:
        path = self.root / run_id / "events.jsonl"
        if not path.exists():
            return []
        events: list[RunEvent] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            value = json.loads(line)
            events.append(RunEvent(value["run_id"], value["event_id"], Stage(value["stage"]), value["status"], value.get("payload", {}), value.get("created_at", ""), value.get("schema_version", "1")))
        return events

    def mark_completed(self, run_id: str) -> None:
        self.append_event(RunEvent(run_id, "run-complete", Stage.REPORT, "COMPLETE", {}))
