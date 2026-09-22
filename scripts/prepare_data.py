from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_HISTORY_FIELDS = [
    "Context",
    "Preconditions",
    "Trigger",
    "Expected Invariant",
    "Observed Failure",
    "Failure Mechanism",
    "Oracle",
    "Oracle Provenance",
    "Test Strategy",
    "Evidence References",
    "Confidence",
]

HISTORICAL_CASES = [
    ("PySnooper", "2"),
    ("PySnooper", "3"),
    ("cookiecutter", "1"),
    ("cookiecutter", "2"),
    ("cookiecutter", "3"),
    ("cookiecutter", "4"),
]


def parse_info(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(errors="replace").splitlines():
        match = re.match(r"\s*([A-Za-z_]+)\s*=\s*\"?(.*?)\"?\s*$", line)
        if match:
            result[match.group(1)] = match.group(2).strip('"')
    return result


def git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        errors="replace",
    )
    return completed.stdout


def clone_project(url: str, destination: Path) -> None:
    if (destination / ".git").exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", url, str(destination)], check=True, capture_output=True, text=True)


def _allowed(path: Path, excluded_paths: set[str]) -> bool:
    rel = path.as_posix()
    if rel in excluded_paths:
        return False
    if any(part in {".git", "env", "env39", "build", "dist", "__pycache__", ".pytest_cache"} or part.endswith(".egg-info") for part in path.parts):
        return False
    if path.name.startswith("bugsinpy_") or path.name.endswith(".pyc"):
        return False
    return path.suffix.lower() in {".py", ".md", ".rst", ".txt", ".toml", ".ini", ".cfg", ".yaml", ".yml", ".json"}


def build_target_context(repo: Path, excluded_paths: set[str] | None = None) -> str:
    excluded_paths = excluded_paths or set()
    chunks: list[str] = []
    total = 0
    for path in sorted(p for p in repo.rglob("*") if p.is_file() and _allowed(p.relative_to(repo), excluded_paths)):
        try:
            content = path.read_text(errors="replace")
        except OSError:
            continue
        if len(content) > 8000:
            content = content[:8000] + "\n...[file truncated]"
        chunk = f"FILE: {path.relative_to(repo)}\n```\n{content}\n```\n"
        if total + len(chunk) > 45000:
            break
        chunks.append(chunk)
        total += len(chunk)
    return "\n".join(chunks)


def _evidence(text: str, provenance: str = "direct") -> dict[str, str]:
    return {"text": text, "provenance": provenance}


def _test_summary(test_text: str) -> str:
    lines = [line.strip() for line in test_text.splitlines() if line.strip() and not line.strip().startswith("#")]
    return " ".join(lines[:14])[:2200]


def history_record(project: str, bug_id: str, benchmark_root: Path, repo: Path) -> tuple[dict, dict]:
    bug_dir = benchmark_root / "projects" / project / "bugs" / bug_id
    info = parse_info(bug_dir / "bug.info")
    buggy = info["buggy_commit_id"]
    fixed = info["fixed_commit_id"]
    test_file = info["test_file"].split(";")[0]
    try:
        test_text = git(repo, "show", f"{fixed}:{test_file}")
    except subprocess.CalledProcessError:
        test_text = "Regression test source unavailable in fixed revision."
    diff = git(repo, "diff", "--unified=4", buggy, fixed, "--", ":(exclude)*.lock")[:7000]
    subject = git(repo, "log", "-1", "--format=%s", fixed).strip()
    changed = git(repo, "diff", "--name-only", buggy, fixed).splitlines()
    history_id = f"{project}:{bug_id}"
    refs = [
        f"{project}/bugs/{bug_id}/bug.info",
        f"{project}@{fixed}:{test_file}",
        f"git diff {buggy[:12]}..{fixed[:12]}",
    ]
    raw = {
        "history_id": history_id,
        "project": project,
        "bug_id": bug_id,
        "bug_report": "No standalone issue text is shipped by BugsInPy; the fixed commit subject is used as the available historical report surrogate.",
        "commit_subject": subject,
        "buggy_commit_id": buggy,
        "fixed_commit_id": fixed,
        "fix_summary": f"The fixed revision changes {', '.join(changed[:8]) or 'the project source'}; exact diff is retained in the evidence reference.",
        "regression_test_summary": _test_summary(test_text),
        "source_references": refs,
        "evidence": {"regression_test": test_text[:5000], "fix_diff": diff},
    }
    structured = {
        "history_id": history_id,
        "project": project,
        "bug_id": bug_id,
        "buggy_commit_id": buggy,
        "fixed_commit_id": fixed,
        "Context": _evidence(f"Historical {project} bug {bug_id}; changed paths: {', '.join(changed[:10]) or 'not listed'}.", "direct from fix diff"),
        "Preconditions": _evidence(_test_summary(test_text), "inferred from historical regression test"),
        "Trigger": _evidence(_test_summary(test_text), "direct from historical regression test"),
        "Expected Invariant": _evidence("The behavior asserted by the historical regression test should hold.", "historical test oracle"),
        "Observed Failure": _evidence(f"The historical regression test was added or changed at fixed revision {fixed[:12]} to distinguish the fixed behavior from the buggy revision.", "inferred from revision pair"),
        "Failure Mechanism": _evidence(diff[:3500], "inferred from fix diff; not independently validated for the target"),
        "Oracle": _evidence(_test_summary(test_text), "direct from historical regression test"),
        "Oracle Provenance": _evidence("Historical regression test only; target truth must be established independently.", "direct methodological label"),
        "Test Strategy": _evidence(f"Run {test_file} against buggy and fixed revisions without changing the test.", "direct from benchmark metadata"),
        "Evidence References": _evidence("; ".join(refs), "direct repository references"),
        "Confidence": _evidence("0.80 for the historical case description; lower for transfer to a new target.", "calibrated judgment"),
    }
    return raw, structured


def validate_history_records(records: Iterable[dict]) -> list[str]:
    errors = []
    for index, record in enumerate(records):
        if not record.get("history_id"):
            errors.append(f"record {index} missing history_id")
        for field in REQUIRED_HISTORY_FIELDS:
            value = record.get(field)
            if not isinstance(value, dict) or not value.get("text") or not value.get("provenance"):
                errors.append(f"record {index} missing evidence-bearing {field}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, default=ROOT / "vendor" / "BugsInPy")
    parser.add_argument("--target-repo", type=Path, default=ROOT / "workspace" / "harness-pysnooper-buggy" / "PySnooper")
    parser.add_argument("--target-project", default="PySnooper")
    parser.add_argument("--target-bug", default="1")
    args = parser.parse_args()

    output = ROOT / "data"
    (output / "target_context").mkdir(parents=True, exist_ok=True)
    (output / "evaluator_truth").mkdir(parents=True, exist_ok=True)
    (ROOT / "artifacts" / "harness").mkdir(parents=True, exist_ok=True)
    (ROOT / "vendor" / "upstream_projects").mkdir(parents=True, exist_ok=True)

    project_urls = {}
    for project in {p for p, _ in HISTORICAL_CASES} | {args.target_project}:
        project_info = parse_info(args.benchmark / "projects" / project / "project.info")
        url = project_info["github_url"]
        project_urls[project] = url
        clone_project(url, ROOT / "vendor" / "upstream_projects" / project)

    raw_records, structured_records = [], []
    for project, bug_id in HISTORICAL_CASES:
        raw, structured = history_record(project, bug_id, args.benchmark, ROOT / "vendor" / "upstream_projects" / project)
        raw_records.append(raw)
        structured_records.append(structured)

    errors = validate_history_records(structured_records)
    if errors:
        raise SystemExit("invalid structured data: " + "; ".join(errors))

    target_info = parse_info(args.benchmark / "projects" / args.target_project / "bugs" / args.target_bug / "bug.info")
    target_context = build_target_context(args.target_repo, {target_info["test_file"]})
    (output / "target_context" / f"{args.target_project}-{args.target_bug}.txt").write_text(target_context)

    manifest = {
        "source": "https://github.com/soarsmu/BugsInPy",
        "benchmark_revision": git(args.benchmark, "rev-parse", "HEAD").strip(),
        "historical_pool": [r["history_id"] for r in raw_records],
        "target_set": [f"{args.target_project}:{args.target_bug}"],
        "candidate_history_ids_per_target": {f"{args.target_project}:{args.target_bug}": [r["history_id"] for r in raw_records]},
        "runtime": {
            "python": "/opt/anaconda3/bin/python3.9",
            "locale": "LC_ALL=C, PYTHONUTF8=0, PYTHONCOERCECLOCALE=0",
            "test_command": "env39/bin/python -m pytest -q generated_test.py",
        },
        "target": {
            "target_id": f"{args.target_project}:{args.target_bug}",
            "project": args.target_project,
            "bug_id": args.target_bug,
            "buggy_commit_id": target_info["buggy_commit_id"],
            "fixed_commit_id": target_info["fixed_commit_id"],
            "buggy_repo": str(args.target_repo.relative_to(ROOT)),
            "fixed_repo": str((ROOT / "workspace" / "harness-pysnooper-fixed" / "PySnooper").relative_to(ROOT)),
            "test_file_evaluator_only": target_info["test_file"],
            "target_context": str((output / "target_context" / f"{args.target_project}-{args.target_bug}.txt").relative_to(ROOT)),
        },
        "leakage_control": {
            "target_context_excludes": [target_info["test_file"], "bugsinpy_bug.info", "bugsinpy_patchfile.info", "bugsinpy_run_test.sh", "bugsinpy_requirements.txt"],
            "evaluator_only": ["target issue/report", "target fixed revision", "target fix diff", "target regression test", "target changed-file metadata"],
        },
        "historical_selection_note": "Historical cases were retrospectively selected to test transfer feasibility; this experiment does not validate autonomous retrieval.",
        "model": {"name": "deepseek-flash", "endpoint": "https://api.deepseek.com/chat/completions", "temperature": 0.2, "max_tokens": 1800},
    }
    (output / "case_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (output / "historical_raw.json").write_text(json.dumps(raw_records, indent=2, ensure_ascii=False) + "\n")
    (output / "historical_structured.json").write_text(json.dumps(structured_records, indent=2, ensure_ascii=False) + "\n")
    (output / "evaluator_truth" / f"{args.target_project}-{args.target_bug}.json").write_text(json.dumps({"target": manifest["target"], "raw_bug_info": target_info}, indent=2) + "\n")
    print(json.dumps({"historical": len(raw_records), "target": manifest["target"]["target_id"], "context_chars": len(target_context)}))


if __name__ == "__main__":
    main()
