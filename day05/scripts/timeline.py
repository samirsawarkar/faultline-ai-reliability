#!/usr/bin/env python3
"""CLI timeline viewer: reconstruct a run from the store.

    python scripts/timeline.py                 # the failed demo run
    python scripts/timeline.py --ok            # the successful demo run
    python scripts/timeline.py --db evidence/trace.db --trace <id>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from faultline_store import TraceStore, build_store, render_timeline  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=str, help="path to a trace.db (default: build in memory)")
    ap.add_argument("--trace", type=str, help="trace_id to view")
    ap.add_argument("--ok", action="store_true", help="view the successful demo run")
    args = ap.parse_args()

    if args.db:
        store = TraceStore(args.db)
        trace_id = args.trace
        if trace_id is None:
            row = (store.conn.execute("SELECT trace_id FROM traces WHERE status='error' "
                                      "ORDER BY trace_id LIMIT 1").fetchone())
            trace_id = row["trace_id"] if row else None
    else:
        store, ok_id, fail_id = build_store()
        trace_id = args.trace or (ok_id if args.ok else fail_id)

    if not trace_id:
        print("no trace to view", file=sys.stderr)
        return 1
    sys.stdout.write(render_timeline(store, trace_id))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
