"""Run isolated per-day pytest suites and write a timing-free test report."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FAST_DAYS = (1, 4, 13, 21, 25, 26, 27)
FULL_DAYS = tuple(range(1, 28))


def _dump(path: Path, value) -> None:
    path.parent.mkdir(exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def run(profile: str) -> dict:
    days = FAST_DAYS if profile == "fast" else FULL_DAYS
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "0"
    records = []
    for day in days:
        suite = f"day{day:02d}/tests/"
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", suite, "-q"],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
        )
        combined = completed.stdout + completed.stderr
        match = re.search(r"(\d+) passed", combined)
        count = int(match.group(1)) if match else 0
        record = {
            "day": day,
            "suite": suite,
            "passed": completed.returncode == 0,
            "test_count": count,
        }
        records.append(record)
        print(
            f"{suite}: {'green' if record['passed'] else 'red'} "
            f"({record['test_count']} tests)"
        )
        if completed.returncode != 0:
            raise RuntimeError(f"{suite} failed:\n{combined}")
    total = sum(record["test_count"] for record in records)
    return {
        "profile": profile,
        "day_range": [min(days), max(days)],
        "suites": records,
        "collected": total,
        "passed": total,
        "passed_all": all(record["passed"] for record in records),
        "python_hash_seed": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("fast", "full"), required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = run(args.profile)
    _dump(ROOT / args.output, report)
    print(
        f"{args.profile} test gate: {report['passed']}/"
        f"{report['collected']} passed"
    )


if __name__ == "__main__":
    main()
