#!/usr/bin/env python3
"""Regenerate Day-6 evidence.

Deterministic (CI byte-diffs these):
  evidence/bundle_simulator.json   the replay bundle (capture)
  evidence/replay_simulator.json   the replay output (trace + final state)
  evidence/replay_report.json      the replay-difference report (diff PATHS)

Informational (NOT byte-diffed):
  evidence/environment.json        captured runtime versions (python/platform)

The simulator bundle is byte-reproducible; a real-provider bundle would not be,
which is exactly the point — so we commit the reproducible one and REPORT the
boundary rather than committing a non-reproducible bundle.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from faultline_replay import (  # noqa: E402
    build_report,
    canonical_bytes,
    capture_run,
    diff_summary,
    replay_bundle,
    runtime_environment,
    save,
)

EVID = ROOT / "evidence"
SEED, TASK = 6, "sum the archive"


def _write_json(path: Path, obj) -> None:
    data = (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(data)
    print(f"wrote {len(data):6d} B -> {path.relative_to(ROOT)}")


def main() -> int:
    EVID.mkdir(exist_ok=True)

    bundle = capture_run("simulator", SEED, TASK)
    save(bundle, str(EVID / "bundle_simulator.json"))
    print(f"wrote {len(canonical_bytes(bundle)):6d} B -> evidence/bundle_simulator.json")

    replayed = replay_bundle(bundle)
    verify = diff_summary(bundle["trace"], replayed["trace"])
    _write_json(EVID / "replay_simulator.json", {
        "replayed_trace": replayed["trace"],
        "final_state": replayed["final_state"],
        "calls_consumed": replayed["calls_consumed"],
        "matches_captured_trace": verify["equal"],
        "diff_count": verify["diff_count"],
    })

    report = build_report()
    _write_json(EVID / "replay_report.json", report)

    # Informational only; excluded from the CI byte-diff.
    _write_json(EVID / "environment.json", runtime_environment())

    print(f"\nsimulator replay exact: {verify['equal']}   "
          f"report claims_hold: {report['claims_hold']}")
    return 0 if (verify["equal"] and report["claims_hold"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
