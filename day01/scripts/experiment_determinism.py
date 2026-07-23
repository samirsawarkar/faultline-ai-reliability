#!/usr/bin/env python3
"""Attack experiment: generate 20 seeds twice, in two independent processes
with DIFFERENT PYTHONHASHSEED, and prove byte-identical output.

Writes evidence/determinism_report.txt. Exits non-zero if any seed drifts.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEEDS = range(20)

_CHILD = (
    "import sys; sys.path.insert(0, r'%s');"
    "from faultline import build_env, canonical_bytes;"
    "import hashlib;"
    "print('\\n'.join("
    "  f'{s} {hashlib.sha256(canonical_bytes(build_env(s))).hexdigest()}'"
    "  for s in range(20)))"
) % str(ROOT)


def child_run(hashseed: str) -> str:
    env = dict(os.environ, PYTHONHASHSEED=hashseed)
    out = subprocess.run([sys.executable, "-c", _CHILD],
                         capture_output=True, text=True, check=True, env=env)
    return out.stdout.strip()


def main() -> int:
    run_a = child_run("0")          # process 1, hashseed 0
    run_b = child_run("random")     # process 2, hashseed randomized
    identical = run_a == run_b

    lines = [
        "FAULTLINE Day 1 -- determinism experiment",
        "=========================================",
        f"seeds tested        : {list(SEEDS)}",
        "runs                : 2 (separate OS processes)",
        "run A PYTHONHASHSEED : 0",
        "run B PYTHONHASHSEED : random",
        f"byte-identical      : {identical}",
        f"combined-digest A   : {hashlib.sha256(run_a.encode()).hexdigest()}",
        f"combined-digest B   : {hashlib.sha256(run_b.encode()).hexdigest()}",
        "",
        "per-seed sha256 (seed <tab> digest):",
        run_a,
    ]
    report = "\n".join(lines) + "\n"
    (ROOT / "evidence" / "determinism_report.txt").write_text(report)
    sys.stdout.write(report)
    return 0 if identical else 1


if __name__ == "__main__":
    raise SystemExit(main())
