from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..application.replay_pipeline import ReplayPipeline
from ..config.loader import load_config
from ..domain.enums import Arm


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay preserved Experiment 4 artifacts without model calls")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--arm", choices=[Arm.STRICT_PLANNER.value, Arm.BUDGET_MATCHED_DIRECT.value], default=Arm.STRICT_PLANNER.value)
    args = parser.parse_args(argv)
    config = load_config(args.config)
    summary = ReplayPipeline().replay(config, args.artifacts, Arm(args.arm))
    print(json.dumps(summary.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
