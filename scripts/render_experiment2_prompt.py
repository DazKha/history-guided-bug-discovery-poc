"""Render the current Experiment 2 prompt without calling an LLM or writing artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:  # package import for tests; direct-script import for reviewer commands
    from .run_experiment2 import CONDITIONS, ROOT, prompt_for
except ImportError:
    from run_experiment2 import CONDITIONS, ROOT, prompt_for


def render_prompt(condition: str, attempt: int, root: Path = ROOT) -> tuple[str, str]:
    """Return the current committed prompt and its SHA-256 digest."""

    if condition not in CONDITIONS:
        raise ValueError(f"unknown condition: {condition}")
    if not isinstance(attempt, int) or attempt < 1:
        raise ValueError("attempt must be a positive integer")
    context = (root / "data/experiment2_target_context/PySnooper-1.txt").read_text(encoding="utf-8")
    raw = json.loads((root / "data/experiment2_historical_raw.json").read_text(encoding="utf-8"))
    structured = json.loads((root / "data/experiment2_historical_structured.json").read_text(encoding="utf-8"))
    prompt = prompt_for(condition, context, raw, structured, attempt)
    return prompt, hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def _is_within(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
    except ValueError:
        return False
    return True


def write_prompt(path: Path, prompt: str, root: Path = ROOT) -> Path:
    """Write an explicitly requested prompt file without overwriting artifacts."""

    output = Path(path).expanduser().resolve()
    if output.exists():
        raise ValueError(f"refusing to overwrite existing prompt output: {output}")
    forbidden_roots = (root / "artifacts").resolve(), (root / "generated_tests").resolve()
    if any(_is_within(output, directory) for directory in forbidden_roots):
        raise ValueError("refusing to write a rendered prompt inside artifacts/ or generated_tests/")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(prompt, encoding="utf-8")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the current Experiment 2 prompt without an LLM call")
    parser.add_argument("--condition", choices=sorted(CONDITIONS), required=True)
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--output", type=Path, help="optional new prompt file outside artifacts/ and generated_tests/")
    args = parser.parse_args(argv)
    try:
        prompt, prompt_hash = render_prompt(args.condition, args.attempt)
        output = write_prompt(args.output, prompt) if args.output else None
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(f"Prompt source: current committed scripts/run_experiment2.py")
    print(f"Condition: {args.condition} ({CONDITIONS[args.condition]})")
    print(f"Attempt: {args.attempt}")
    print(f"SHA256: {prompt_hash}")
    if output:
        print(f"Saved prompt: {output}")
    print(f"\n{prompt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
