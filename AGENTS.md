# Project Mission

Build a small, reproducible empirical proof for history-guided proactive bug discovery.

The final experiment must compare:

1. Target-only
2. Raw Historical RAG
3. Structured History-Guided

using real historical bugs and held-out buggy/fixed target revisions.

## Scientific constraints

- Never fabricate results.
- Never leak target issue/fix/regression test into generation.
- Keep the same model, target context, attempt count, and repair budget across conditions.
- The strongest verification signal is:
  T(B) = FAIL
  T(F) = PASS
- A test failing due to syntax/import/setup errors does not count.
- Raw-history and structured-history conditions must use the same underlying historical cases.
- Small negative results are acceptable.

## Scope constraints

Do not spend time on:
- UI
- Streamlit
- knowledge graphs
- fine-tuning
- Jev
- multi-agent orchestration
- large vector databases

Prefer the smallest implementation that produces real executable evidence.

## Dataset priority

1. BugsInPy
2. TestExplora
3. Defects4J

Use official documentation/repositories and record sources in research_log.md.

## Security

Read DEEPSEEK_API_KEY from the environment.
Never print, log, or commit secrets.

## Required outputs

- README.md
- research_log.md
- data/case_manifest.json
- data/historical_raw.json
- data/historical_structured.json
- results/results.csv
- results/summary.csv
- results/failure_analysis.md
- FOLLOWUP_REPORT.md
- generated tests
- execution logs

## Working style

- Verify the dataset harness before building the pipeline.
- Work milestone by milestone.
- Run real commands and tests.
- Commit working milestones.
- If blocked, diagnose and use documented fallback paths.
- Never claim success without execution evidence.