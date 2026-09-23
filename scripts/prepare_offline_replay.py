from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = {
    "exploratory": ROOT / "artifacts/experiment2_llm_run1/PySnooper_1",
    "final": ROOT / "artifacts/experiment2_llm/PySnooper_1",
    "loop1": ROOT / "artifacts/experiment2_llm_loop1/PySnooper_1",
    "replication2b": ROOT / "artifacts/experiment2_llm_replication2b/PySnooper_1",
    "replication2c": ROOT / "artifacts/experiment2_llm_replication2c/PySnooper_1",
}


def prepare() -> list[dict]:
    selected = json.loads((ROOT / "data/experiment3_conditional_hypotheses.json").read_text())
    out_dir = ROOT / "artifacts/experiment3_llm/conditional/C1"
    out_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for item in selected:
        source = ROOT / item["source_artifact"]
        raw = json.loads(source.read_text())
        test_path = raw.get("test_path", "")
        if source.parent.name == "PySnooper_1" and source.parent.parent.name == "experiment2_llm_run1":
            test_path = test_path.replace("generated_tests/experiment2/", "generated_tests/experiment2_run1/")
        record = dict(item)
        record.update({
            "arm": "C1",
            "test_id": f"{item['hypothesis_id']}-direct-replay",
            "trigger_id": "direct-replay",
            "status": raw.get("status", "MODEL_ERROR"),
            "test_path": test_path,
            "test_code": raw.get("test_code", ""),
            "llm": {"model": "replayed-experiment2-artifact", "request_count": 0, "usage": {}},
            "replay_source": item["source_artifact"],
        })
        path = out_dir / f"{item['hypothesis_id']}__C1.json"
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
        records.append(record)
    return records


if __name__ == "__main__":
    print(json.dumps({"replayed": len(prepare()), "arm": "conditional/C1"}))

