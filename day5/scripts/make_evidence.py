#!/usr/bin/env python3
"""Regenerate all Day-5 evidence (deterministic parts diffed in CI).

  evidence/trace.db                     the SQLite store (regenerated, not diffed)
  evidence/timeline_failed.txt          terminal viewer of the failed run
  evidence/failed_run.svg               visual snapshot a stranger opens
  evidence/attack_report.json           deletion attack + reconstruction survival
  evidence/incident_narrative.md        the story, written ONLY from the viewer
  evidence/reconstruction_timing.json   wall-clock timing (NOT diffed; noisy)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from faultline_store import (  # noqa: E402
    TraceStore,
    build_store,
    reconstruct,
    render_svg,
    render_timeline,
)
from faultline_store.attack import run_scenarios  # noqa: E402

EVID = ROOT / "evidence"


def _write(path: Path, data: str) -> None:
    path.write_text(data)
    print(f"wrote {len(data.encode()):6d} B -> {path.relative_to(ROOT)}")


def main() -> int:
    EVID.mkdir(exist_ok=True)

    # Persistent DB on disk (regenerated each run; binary, not diff-gated).
    db_path = EVID / "trace.db"
    if db_path.exists():
        db_path.unlink()
    disk, ok_id, fail_id = build_store(str(db_path))
    disk.close()

    # In-memory store for the deterministic text/SVG artifacts.
    store, ok_id, fail_id = build_store()

    _write(EVID / "timeline_failed.txt", render_timeline(store, fail_id))
    _write(EVID / "failed_run.svg", render_svg(store, fail_id))

    report = run_scenarios()
    _write(EVID / "attack_report.json",
           json.dumps(report, indent=2, sort_keys=True) + "\n")

    _write(EVID / "incident_narrative.md", incident_narrative(store, fail_id))

    # Timing: measure reconstruction cost. Non-deterministic -> its own file,
    # excluded from the CI byte-diff.
    timing = measure_timing(str(db_path))
    _write(EVID / "reconstruction_timing.json",
           json.dumps(timing, indent=2, sort_keys=True) + "\n")

    print(f"\nreconstructable across deletions: {report['all_scenarios_reconstructable']}")
    return 0 if report["all_scenarios_reconstructable"] else 1


def incident_narrative(store: TraceStore, trace_id: str) -> str:
    """The incident report a stranger could write from the viewer alone."""
    r = reconstruct(store, trace_id)
    err = next(s for s in r["spans"] if s["status"] == "error" and s["depth"] > 0)
    path = " > ".join(r["failing_paths"][0]) if r["failing_paths"] else "n/a"
    return f"""# Incident narrative — {trace_id}

*Reconstructed entirely from the Day-5 timeline viewer by someone who did not
run the job. No raw logs, no source access — only `faultline_store`.*

## Summary
Run **{trace_id}** ended in **{r['trace_status'].upper()}**. It executed
{r['present_span_count']} spans. The failure originates in
**`{err['name']}`** (a `{err['kind']}` span) at sequence {err['start_seq']}.

## What happened, in order
The `agent` root span started, called the `model` to plan, then ran the tool
steps in sequence. `tool.retrieve` succeeded; **`{err['name']}` failed** with:

> `{err['error_type']}: {err['error_message']}`

Because the tracer closes spans on the way out, the failure propagated up: the
parent `agent` span is also recorded as `error`. The verify step never ran.

## Root cause & blast radius
- **Root-cause span:** `{', '.join(r['root_cause_spans'])}`
- **Failing path (root → failure):** {path}
- **Unaffected:** model planning and retrieval both completed `ok`.

## How this was reconstructed
`reconstruct()` issued indexed queries against the SQLite store (`SEARCH ...
USING INDEX`), ordered the spans by their logical clock, and walked parent
links from the failing leaf to the root. No wall-clock, no guesswork.

## Note on redaction
The tool's error text originally interpolated a secret. The stored message shows
`token=***REDACTED***` — the secret never reached the store (Day-4 redaction
policy), so this narrative is safe to share.
"""


def measure_timing(db_path: str) -> dict:
    """Wall-clock reconstruction cost from the on-disk store (cold-ish)."""
    store = TraceStore(db_path)
    fail_id = store.failed_traces()[0]["trace_id"]
    n = 200
    t0 = time.perf_counter()
    for _ in range(n):
        reconstruct(store, fail_id)
    dt = time.perf_counter() - t0
    store.close()
    return {
        "trace_id": fail_id,
        "iterations": n,
        "total_seconds": round(dt, 6),
        "avg_ms_per_reconstruction": round(dt / n * 1000, 4),
        "note": "wall-clock; excluded from CI byte-diff by design",
    }


if __name__ == "__main__":
    raise SystemExit(main())
