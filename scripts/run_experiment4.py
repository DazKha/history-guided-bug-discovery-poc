"""Backward-compatible wrapper for the reusable discovery-engine CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from history_guided_bug_discovery.cli.run import main as run_main


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iteration", type=int, choices=[1, 2, 3], default=3, help="retained for compatibility; new runs use the versioned config")
    parser.add_argument("--arm", choices=["C1", "C1B", "C2", "both"], default="both")
    args = parser.parse_args()
    arm = "C1_BUDGETED" if args.arm == "C1B" else args.arm
    return run_main(["--config", str(ROOT / "configs/experiment4.json"), "--arm", arm])


if __name__ == "__main__":
    raise SystemExit(main())
