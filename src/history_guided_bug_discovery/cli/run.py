from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from ..adapters.benchmark_evaluator import BenchmarkEvaluator
from ..adapters.bugsinpy import BugsInPyTargetAdapter
from ..adapters.providers import create_provider
from ..adapters.json_artifact_store import JsonArtifactStore
from ..adapters.subprocess_executor import SubprocessExecutor
from ..application.discovery_pipeline import DiscoveryPipeline
from ..config.loader import load_config
from ..domain.enums import Arm


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the history-guided discovery pipeline")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--arm", choices=[arm.value for arm in Arm] + ["both"], default=Arm.STRICT_PLANNER.value)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)
    config = load_config(args.config)
    provider = create_provider(config)
    arms = list(Arm) if args.arm == "both" else [Arm(args.arm)]
    summaries = []
    for arm in arms:
        run_config = replace(config, run_id=config.run_id if len(arms) == 1 else f"{config.run_id}-{arm.value}")
        store = JsonArtifactStore(run_config.paths.artifact_root)
        evaluator = BenchmarkEvaluator(tuple(run_config.target.get("source_path_markers", ())))
        pipeline = DiscoveryPipeline(run_config, provider, SubprocessExecutor(), evaluator, store, BugsInPyTargetAdapter(run_config.paths.target_context, run_config.generation_visible_manifest, str(run_config.target.get("python", "python3")), str(run_config.target.get("runner", "pytest"))))
        summaries.append(pipeline.run(arm, resume=args.resume).to_dict())
    print(json.dumps({"runs": summaries}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
