# Experiment 4 append-only correction note

The raw `results/experiment4_results.csv` was audited before subsequent work. Its authoritative final iteration-3 C2 rows are:

- 5 F2P
- 3 P2P
- 5 mechanical failures
- 2 model-output failures
- 0 F2F

Two report inconsistencies were corrected without changing raw CSVs, generated tests, execution logs, evaluator code, or historical results:

1. `results/experiment4_summary.md` incorrectly stated one final C2 F2F; it now states zero.
2. `results/experiment4_failure_analysis.md` had a stale per-hypothesis final-C2 table; it now matches the raw rows by hypothesis.

The prior reports and raw artifacts remain in git history. This note is append-only and records the correction before subsequent generation work began.
