from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..application.replay_pipeline import ReplayPipeline
from ..config.loader import load_config
from ..domain.enums import Arm


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate or replay an Experiment 4 artifact batch")
    parser.add_argument("--config", type=Path, default=Path("configs/experiment4.json"))
    parser.add_argument("--iteration", type=int, default=3)
    parser.add_argument("--arms", default="C1,C2")
    parser.add_argument("--output-suffix", default="")
    parser.add_argument("--artifacts", type=Path)
    args = parser.parse_args(argv)
    config = load_config(args.config)
    artifact_dir = args.artifacts or config.repository_root / "artifacts" / "experiment4" / f"iteration{args.iteration}"
    if not artifact_dir.is_absolute():
        artifact_dir = config.repository_root / artifact_dir
    results = {}
    for label in (part.strip() for part in args.arms.split(",")):
        arm = Arm.BUDGET_MATCHED_DIRECT if label == "C1_BUDGETED" else Arm(label)
        results[label] = ReplayPipeline().replay(config, artifact_dir, arm).to_dict()
    print(json.dumps({"iteration": args.iteration, "results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
