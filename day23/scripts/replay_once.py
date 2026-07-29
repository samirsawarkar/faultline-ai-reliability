"""Reproduce one incident from the committed scenario file and print its digest."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in ("", "../day04", "../day14", "../day16", "../day20", "../day21"):
    sys.path.insert(0, str((ROOT / rel).resolve()))

from faultline_cascade import CascadeConfig, run_cascade  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True)
    args = parser.parse_args()
    scenario = json.loads(Path(args.scenario).read_text(encoding="utf-8"))
    result = run_cascade(
        int(scenario["seed"]),
        CascadeConfig(**scenario["config"]).validate(),
    )
    print(
        json.dumps(
            {
                "incident_digest": result["incident_digest"],
                "trace_digest": result["trace_digest"],
                "chain": [event["label"] for event in result["events"]],
                "audit_passed": result["audit"]["passed"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
