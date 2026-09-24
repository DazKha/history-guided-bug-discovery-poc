from __future__ import annotations

import csv
from pathlib import Path

from .aggregate import AggregateSummary


def write_csv(summary: AggregateSummary, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    data = summary.to_dict()
    data.pop("metadata", None)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(data), lineterminator="\n")
        writer.writeheader()
        writer.writerow(data)
    return output
