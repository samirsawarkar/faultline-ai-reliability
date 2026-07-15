#!/usr/bin/env python3
"""Emit example traces + the forced-failure experiment report into evidence/.

  evidence/trace_normal.json         one clean agent/model/tool trace
  evidence/trace_failed.json         one trace with a mid-tool failure
  evidence/forced_failure_report.json  audit of 100 forced-failure runs
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from faultline_trace import (  # noqa: E402
    RiskyToolError,
    STEPS,
    Tracer,
    audit_failed_trace,
    audit_ok_trace,
    run_pipeline,
)

EVID = ROOT / "evidence"
N = 100


def _write(path: Path, data: bytes) -> None:
    path.write_bytes(data)
    print(f"wrote {len(data):6d} bytes -> {path.relative_to(ROOT)}")


def normal_trace() -> None:
    t = Tracer(7)
    run_pipeline(t, task="sum the archive", fail_at=None)
    audit_ok_trace(t.spans)
    _write(EVID / "trace_normal.json", t.to_json())


def failed_trace() -> None:
    t = Tracer(7)
    try:
        run_pipeline(t, task="sum the archive", fail_at="sum", secret="hunter2")
    except RiskyToolError:
        pass
    audit_failed_trace(t.spans)
    blob = t.to_json()
    assert b"hunter2" not in blob
    _write(EVID / "trace_failed.json", blob)


def forced_failure_experiment() -> None:
    runs = []
    all_ok = True
    for seed in range(N):
        fail_at = STEPS[seed % len(STEPS)]
        t = Tracer(seed)
        raised = False
        try:
            run_pipeline(t, task=f"task-{seed}", fail_at=fail_at, secret="hunter2")
        except RiskyToolError:
            raised = True
        report = audit_failed_trace(t.spans)
        leaked = b"hunter2" in t.to_json()
        complete = raised and report["complete"] and not leaked
        all_ok = all_ok and complete
        runs.append({
            "seed": seed, "fail_at": fail_at, "raised": raised,
            "spans": report["spans"], "error_spans": report["error_spans"],
            "open_spans": report["open_spans"], "leaked_secret": leaked,
            "complete_error_span": complete,
        })
    out = {
        "runs": N,
        "all_complete": all_ok,
        "incomplete_traces": [r["seed"] for r in runs if not r["complete_error_span"]],
        "detail": runs,
    }
    _write(EVID / "forced_failure_report.json",
           (json.dumps(out, indent=2, sort_keys=True) + "\n").encode())
    print(f"forced-failure: {N} runs, all_complete={all_ok}")
    if not all_ok:
        raise SystemExit(1)


def main() -> int:
    EVID.mkdir(exist_ok=True)
    normal_trace()
    failed_trace()
    forced_failure_experiment()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
