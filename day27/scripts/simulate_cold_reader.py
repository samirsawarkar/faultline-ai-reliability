"""Execute the REPRODUCE.md cold block in a fresh directory."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "day27"))

from faultline_cold_repro import (  # noqa: E402
    load_protocol,
    run_documented_cold_start,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repository-url",
        default=load_protocol()["repository_url"],
    )
    parser.add_argument(
        "--evidence-directory",
        default="day27/evidence",
    )
    parser.add_argument("--workspace-parent")
    args = parser.parse_args()
    report = run_documented_cold_start(
        repository_url=args.repository_url,
        evidence_directory=ROOT / args.evidence_directory,
        workspace_parent=(
            Path(args.workspace_parent).resolve()
            if args.workspace_parent
            else None
        ),
    )
    print(
        "cold-start simulation "
        f"{'green' if report['passed'] else 'red'}; "
        f"improvisations={report['operator_improvisations']}"
    )
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
