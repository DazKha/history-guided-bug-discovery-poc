"""Verify the recorded Experiment 2 A/B/C evidence without rerunning generation."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
CLEAN_PATH = Path("results/experiment2_replication2.csv")
CUMULATIVE_PATH = Path("results/experiment2_re_evaluated.csv")
CONDITIONS = ("A", "B", "C")
CONDITION_NAMES = {
    "A": "TARGET_ONLY",
    "B": "NAIVE_RAW_HISTORY",
    "C": "STRUCTURED_APPLICABILITY_AWARE",
}
REQUIRED_COLUMNS = {
    "run_label",
    "source_batch",
    "condition",
    "condition_name",
    "hypothesis_matches_true_failure_mechanism",
    "verified_f2p",
}


@dataclass(frozen=True)
class Metrics:
    attempts: int
    mechanism_matches: int
    verified_f2p: int


@dataclass(frozen=True)
class ExpectedMetrics:
    attempts: int
    mechanism_matches: int
    verified_f2p: int


CLEAN_EXPECTED = {
    "A": ExpectedMetrics(attempts=10, mechanism_matches=0, verified_f2p=0),
    "B": ExpectedMetrics(attempts=10, mechanism_matches=1, verified_f2p=0),
    "C": ExpectedMetrics(attempts=10, mechanism_matches=6, verified_f2p=0),
}
CUMULATIVE_EXPECTED = {
    "A": ExpectedMetrics(attempts=25, mechanism_matches=0, verified_f2p=0),
    "B": ExpectedMetrics(attempts=25, mechanism_matches=2, verified_f2p=0),
    "C": ExpectedMetrics(attempts=25, mechanism_matches=15, verified_f2p=2),
}


def _parse_boolean(value: str, *, field: str, row_number: int, allow_blank: bool = False) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "yes", "1"}:
        return True
    if normalized in {"false", "no", "0"} or (allow_blank and normalized == ""):
        return False
    raise ValueError(f"row {row_number}: invalid boolean for {field}: {value!r}")


def _check_run_labels(
    row: Mapping[str, str],
    row_number: int,
    expected_run_label: str | None,
    expected_run_labels: set[str] | None,
) -> None:
    if expected_run_label is not None and row["run_label"] != expected_run_label:
        raise ValueError(
            f"row {row_number}: expected run_label {expected_run_label!r}, "
            f"found {row['run_label']!r}"
        )
    if expected_run_labels is not None and row["run_label"] not in expected_run_labels:
        raise ValueError(
            f"row {row_number}: run_label {row['run_label']!r} is not in "
            f"{sorted(expected_run_labels)!r}"
        )


def verify_csv(
    path: Path,
    *,
    expected_attempts: int,
    expected_metrics: Mapping[str, ExpectedMetrics],
    expected_run_label: str | None = None,
    expected_run_labels: Iterable[str] | None = None,
    expected_source_batches: Iterable[str] | None = None,
) -> dict[str, Metrics]:
    """Derive and verify per-condition metrics from one authoritative CSV."""

    if expected_run_label is not None and expected_run_labels is not None:
        raise ValueError("expected_run_label and expected_run_labels are mutually exclusive")
    if not path.is_file():
        raise ValueError(f"authoritative evidence file is missing: {path}")

    allowed_run_labels = set(expected_run_labels) if expected_run_labels is not None else None
    allowed_source_batches = set(expected_source_batches) if expected_source_batches is not None else None
    expected_conditions = set(expected_metrics)
    if expected_conditions != set(CONDITIONS):
        raise ValueError(f"expected metrics must cover conditions exactly: {CONDITIONS}")

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        actual_columns = set(reader.fieldnames or ())
        missing_columns = sorted(REQUIRED_COLUMNS - actual_columns)
        if missing_columns:
            raise ValueError(f"missing required columns in {path}: {', '.join(missing_columns)}")

        rows_by_condition: dict[str, list[Mapping[str, str]]] = {condition: [] for condition in CONDITIONS}
        for row_number, row in enumerate(reader, start=2):
            condition = row.get("condition", "").strip()
            if condition not in CONDITIONS:
                raise ValueError(f"row {row_number}: unknown condition {condition!r}")
            if row.get("condition_name", "") != CONDITION_NAMES[condition]:
                raise ValueError(
                    f"row {row_number}: condition {condition} must be named "
                    f"{CONDITION_NAMES[condition]!r}, found {row.get('condition_name')!r}"
                )
            _check_run_labels(row, row_number, expected_run_label, allowed_run_labels)
            if allowed_source_batches is not None and row["source_batch"] not in allowed_source_batches:
                raise ValueError(
                    f"row {row_number}: source_batch {row['source_batch']!r} is not in "
                    f"{sorted(allowed_source_batches)!r}"
                )
            _parse_boolean(
                row["hypothesis_matches_true_failure_mechanism"],
                field="hypothesis_matches_true_failure_mechanism",
                row_number=row_number,
            )
            _parse_boolean(row["verified_f2p"], field="verified_f2p", row_number=row_number, allow_blank=True)
            rows_by_condition[condition].append(row)

    present_conditions = {condition for condition, rows in rows_by_condition.items() if rows}
    if present_conditions != set(CONDITIONS):
        raise ValueError(
            f"conditions must be exactly {list(CONDITIONS)!r}; "
            f"present conditions were {sorted(present_conditions)!r}"
        )

    actual: dict[str, Metrics] = {}
    for condition in CONDITIONS:
        rows = rows_by_condition[condition]
        mechanism_matches = sum(
            _parse_boolean(
                row["hypothesis_matches_true_failure_mechanism"],
                field="hypothesis_matches_true_failure_mechanism",
                row_number=0,
            )
            for row in rows
        )
        verified_f2p = sum(
            _parse_boolean(row["verified_f2p"], field="verified_f2p", row_number=0, allow_blank=True)
            for row in rows
        )
        actual[condition] = Metrics(
            attempts=len(rows),
            mechanism_matches=mechanism_matches,
            verified_f2p=verified_f2p,
        )

        expected = expected_metrics[condition]
        if actual[condition].attempts != expected_attempts:
            raise ValueError(
                f"{path}: {condition} expected {expected_attempts} attempts, "
                f"found {actual[condition].attempts}"
            )
        if actual[condition] != Metrics(
            attempts=expected.attempts,
            mechanism_matches=expected.mechanism_matches,
            verified_f2p=expected.verified_f2p,
        ):
            raise ValueError(
                f"{path}: {condition} metrics mismatch: expected "
                f"{expected}, found {actual[condition]}"
            )

    return actual


def verify_recorded_results(root: Path = ROOT) -> dict[str, dict[str, Metrics]]:
    """Verify the clean replication and cumulative recorded evidence bundles."""

    clean = verify_csv(
        root / CLEAN_PATH,
        expected_attempts=10,
        expected_metrics=CLEAN_EXPECTED,
        expected_run_label="replication2",
        expected_source_batches={"replication2b", "replication2c"},
    )
    cumulative = verify_csv(
        root / CUMULATIVE_PATH,
        expected_attempts=25,
        expected_metrics=CUMULATIVE_EXPECTED,
        expected_run_labels={"exploratory", "final", "loop1", "replication2b", "replication2c"},
        expected_source_batches={"exploratory", "final", "loop1", "replication2b", "replication2c"},
    )
    return {"clean_replication": clean, "cumulative": cumulative}


def main() -> int:
    try:
        results = verify_recorded_results()
    except ValueError as error:
        raise SystemExit(f"Core A/B/C evidence verification failed: {error}") from error

    print("Core A/B/C evidence verified from authoritative CSV sources:")
    for dataset_name, metrics_by_condition in results.items():
        print(f"{dataset_name}:")
        for condition in CONDITIONS:
            metrics = metrics_by_condition[condition]
            print(
                f"  {condition}: {metrics.mechanism_matches}/{metrics.attempts} mechanism matches, "
                f"{metrics.verified_f2p} verified F2P"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
