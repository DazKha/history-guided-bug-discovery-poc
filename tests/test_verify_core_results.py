from __future__ import annotations

import csv
from pathlib import Path

import pytest

from scripts.verify_core_results import (
    CLEAN_EXPECTED,
    ROOT,
    verify_csv,
    verify_recorded_results,
)


FIELDS = [
    "run_label",
    "source_batch",
    "condition",
    "condition_name",
    "hypothesis_matches_true_failure_mechanism",
    "verified_f2p",
]
CONDITION_NAMES = {
    "A": "TARGET_ONLY",
    "B": "NAIVE_RAW_HISTORY",
    "C": "STRUCTURED_APPLICABILITY_AWARE",
}


def write_fixture(path: Path, *, attempts: int = 10, omit: str | None = None, malformed: bool = False) -> None:
    fieldnames = [field for field in FIELDS if field != omit]
    rows = []
    for condition in "ABC":
        for attempt in range(attempts):
            row = {
                "run_label": "replication2",
                "source_batch": "replication2b" if attempt < 5 else "replication2c",
                "condition": condition,
                "condition_name": CONDITION_NAMES[condition],
                "hypothesis_matches_true_failure_mechanism": "yes"
                if condition == "C" and attempt < 6
                else "yes"
                if condition == "B" and attempt == 0
                else "no",
                "verified_f2p": "False",
            }
            if malformed and condition == "C" and attempt == 0:
                row["hypothesis_matches_true_failure_mechanism"] = "maybe"
            rows.append({key: value for key, value in row.items() if key in fieldnames})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_recorded_core_results_are_derived_from_authoritative_csvs():
    actual = verify_recorded_results(ROOT)

    assert actual["clean_replication"]["A"].mechanism_matches == 0
    assert actual["clean_replication"]["B"].mechanism_matches == 1
    assert actual["clean_replication"]["C"].mechanism_matches == 6
    assert all(metrics.verified_f2p == 0 for metrics in actual["clean_replication"].values())

    assert actual["cumulative"]["A"].mechanism_matches == 0
    assert actual["cumulative"]["B"].mechanism_matches == 2
    assert actual["cumulative"]["C"].mechanism_matches == 15
    assert actual["cumulative"]["C"].verified_f2p == 2


def test_incorrect_count_is_rejected(tmp_path):
    path = tmp_path / "wrong-count.csv"
    write_fixture(path, attempts=9)

    with pytest.raises(ValueError, match="expected 10 attempts"):
        verify_csv(
            path,
            expected_attempts=10,
            expected_metrics=CLEAN_EXPECTED,
            expected_run_label="replication2",
            expected_source_batches={"replication2b", "replication2c"},
        )


def test_missing_condition_is_rejected(tmp_path):
    path = tmp_path / "missing-condition.csv"
    write_fixture(path)
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    rows = [row for row in rows if row["condition"] != "B"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(ValueError, match="conditions must be exactly"):
        verify_csv(
            path,
            expected_attempts=10,
            expected_metrics=CLEAN_EXPECTED,
            expected_run_label="replication2",
            expected_source_batches={"replication2b", "replication2c"},
        )


@pytest.mark.parametrize(
    ("omit", "malformed", "message"),
    [
        ("verified_f2p", False, "missing required columns"),
        (None, True, "invalid boolean"),
    ],
)
def test_malformed_or_missing_required_fields_are_rejected(tmp_path, omit, malformed, message):
    path = tmp_path / "bad-schema.csv"
    write_fixture(path, omit=omit, malformed=malformed)

    with pytest.raises(ValueError, match=message):
        verify_csv(
            path,
            expected_attempts=10,
            expected_metrics=CLEAN_EXPECTED,
            expected_run_label="replication2",
            expected_source_batches={"replication2b", "replication2c"},
        )
