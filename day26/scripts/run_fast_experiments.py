"""Regenerate a fast research subset and require byte-identical evidence."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "day26"))

from faultline_repro.utils import tree_digest  # noqa: E402

EXPERIMENTS = (
    ("tool_hops", "day07/scripts/run_q1.py", "day07/evidence"),
    ("fallback_quality", "day21/scripts/make_evidence.py", "day21/evidence"),
    ("postmortem_replay", "day25/scripts/make_evidence.py", "day25/evidence"),
)


def _paths(directory: Path):
    return [
        path for path in directory.rglob("*")
        if path.is_file() and path.name != "trace.db"
    ]


def main() -> None:
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "0"
    records = []
    for name, script, evidence_dir in EXPERIMENTS:
        directory = ROOT / evidence_dir
        before = tree_digest(_paths(directory), ROOT)
        completed = subprocess.run(
            [sys.executable, script],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
        )
        after = tree_digest(_paths(directory), ROOT)
        record = {
            "name": name,
            "script": script,
            "evidence_directory": evidence_dir,
            "artifact_count": len(after["files"]),
            "before_digest": before["digest"],
            "after_digest": after["digest"],
            "command_succeeded": completed.returncode == 0,
            "byte_identical": before == after,
        }
        record["passed"] = (
            record["command_succeeded"] and record["byte_identical"]
        )
        records.append(record)
        print(
            f"{name}: {'green' if record['passed'] else 'red'}; "
            f"{record['artifact_count']} artifacts"
        )
        if not record["passed"]:
            raise RuntimeError(
                f"{name} did not reproduce:\n"
                f"{completed.stdout}\n{completed.stderr}"
            )
    report = {
        "profile": "fast",
        "python_hash_seed": 0,
        "experiments": records,
        "passed": all(record["passed"] for record in records),
    }
    output = ROOT / "day26/evidence/fast_experiment_report.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(
        json.dumps(report, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
