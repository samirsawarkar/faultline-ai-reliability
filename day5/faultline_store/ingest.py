"""Produce Day-4 traces and ingest them into a TraceStore.

Day 5 stores what Day 4 emits: we import the Day-4 tracer, run the deterministic
pipeline (one clean run, one mid-tool failure), and load both into the store.
No LLM, no clock -> the fixture is byte-reproducible.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Tuple

from .store import TraceStore

_DAY4 = Path(__file__).resolve().parents[2] / "day4"


def _day4():
    if str(_DAY4) not in sys.path:
        sys.path.insert(0, str(_DAY4))
    import faultline_trace as ft  # noqa: E402
    return ft


def make_traces() -> Tuple[dict, dict]:
    """Return (ok_trace, failed_trace) as Day-4 to_dict() payloads."""
    ft = _day4()

    # Distinct seeds -> distinct trace_ids (the id derives from the seed), so
    # the two runs coexist in the store instead of one overwriting the other.
    ok = ft.Tracer(100)
    ft.run_pipeline(ok, task="sum the archive", fail_at=None)

    failed = ft.Tracer(7)
    try:
        ft.run_pipeline(failed, task="sum the archive", fail_at="sum", secret="hunter2")
    except ft.RiskyToolError:
        pass

    return ok.to_dict(), failed.to_dict()


def build_store(path: str = ":memory:") -> Tuple[TraceStore, str, str]:
    """Build a store with the ok + failed traces. Returns (store, ok_id, fail_id)."""
    ok, failed = make_traces()
    store = TraceStore(path)
    ok_id = store.ingest_trace(ok)
    fail_id = store.ingest_trace(failed)
    return store, ok_id, fail_id
