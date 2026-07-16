#!/usr/bin/env python3
"""Materialize the on-disk SQLite trace store at evidence/trace.db.

    python scripts/build_store.py
    sqlite3 evidence/trace.db "SELECT trace_id,status,span_count FROM traces;"
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from faultline_store import build_store  # noqa: E402


def main() -> int:
    db = ROOT / "evidence" / "trace.db"
    db.parent.mkdir(exist_ok=True)
    if db.exists():
        db.unlink()
    store, ok_id, fail_id = build_store(str(db))
    traces = store.conn.execute(
        "SELECT trace_id, status, span_count FROM traces ORDER BY trace_id").fetchall()
    for t in traces:
        print(f"{t['trace_id']}  status={t['status']:5}  spans={t['span_count']}")
    store.close()
    print(f"\nstore -> {db.relative_to(ROOT)}  (ok={ok_id}, failed={fail_id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
