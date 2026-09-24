from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..application.replay_pipeline import ReplayPipeline
from ..config.loader import load_config
from ..domain.enums import Arm
from ..reporting.csv_report import write_csv
from ..reporting.markdown import write_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate idempotent CSV, JSON, and Markdown reports")
    parser.add_argument("--config", type=Path, default=Path("configs/experiment4.json"))
    parser.add_argument("--run-id", default="experiment4-final")
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts/experiment4/iteration3"))
    parser.add_argument("--arm", choices=[Arm.STRICT_PLANNER.value, Arm.BUDGET_MATCHED_DIRECT.value], default=Arm.STRICT_PLANNER.value)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    config = load_config(args.config, Path.cwd())
    summary = ReplayPipeline().replay(config, args.artifacts, Arm(args.arm))
    output = args.output_dir or Path("artifacts") / "reports" / args.run_id / args.arm
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(json.dumps(summary.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(summary, output / "summary.csv")
    write_markdown(summary, output / "summary.md")
    print(json.dumps({"output_dir": str(output), "summary": summary.to_dict()}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
