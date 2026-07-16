"""FAULTLINE Day 5: SQLite trace store + timeline viewer + reconstruction.

    TraceStore(path)          -> indexed SQLite store of Day-4 spans
    build_store(path)         -> store preloaded with an ok + a failed trace
    reconstruct(store, tid)   -> structured 'what failed, where' from the store
    render_timeline(store,tid)-> terminal timeline viewer (str)
    render_svg(store, tid)    -> deterministic SVG snapshot (str)
"""
from .ingest import build_store, make_traces
from .reconstruct import reconstruct
from .render import render_svg
from .store import TraceStore
from .viewer import render_timeline

__all__ = [
    "TraceStore",
    "build_store",
    "make_traces",
    "reconstruct",
    "render_timeline",
    "render_svg",
]
