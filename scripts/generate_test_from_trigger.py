from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.deepseek_client import DeepSeekClient
from scripts.experiment3_runner import parse_test_response, test_prompt


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hypothesis", type=Path, required=True)
    parser.add_argument("--trigger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    record = json.loads(args.hypothesis.read_text())
    trigger = json.loads(args.trigger.read_text())
    context = (ROOT / "data/experiment2_target_context/PySnooper-1.txt").read_text()
    client = DeepSeekClient(model="deepseek-flash", temperature=0.2)
    parsed = parse_test_response(client.generate(test_prompt(record, trigger, context), max_tokens=2200).content)
    if parsed["status"] == "TEST":
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(parsed["test_code"] + "\n")
    print(json.dumps({"status": parsed["status"], "output": str(args.output)}))


if __name__ == "__main__":
    main()

