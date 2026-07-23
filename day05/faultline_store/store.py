"""TraceStore — persist Day-4 spans in SQLite and query them by index.

The store is the durable form of a trace: a Day-4 `Tracer` holds one run in
memory; ingesting it here makes it survive the process, and the indices make
reconstruction cheap for someone who wasn't there when it ran.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List, Optional

from .schema_sql import SCHEMA


def _json(obj: Any) -> Optional[str]:
    if obj is None:
        return None
    return json.dumps(obj, sort_keys=True, ensure_ascii=True)


class TraceStore:
    def __init__(self, path: str = ":memory:"):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    # --- ingest --------------------------------------------------------------
    def ingest_trace(self, trace: Dict[str, Any]) -> str:
        """Ingest a Day-4 `Tracer.to_dict()` payload. Idempotent per trace_id."""
        spans = trace["spans"]
        trace_id = trace["trace_id"]
        status = "error" if any(s["status"] == "error" for s in spans) else "ok"
        with self.conn:
            self.conn.execute("DELETE FROM spans WHERE trace_id=?", (trace_id,))
            self.conn.execute("DELETE FROM traces WHERE trace_id=?", (trace_id,))
            self.conn.execute(
                "INSERT INTO traces(trace_id, seed, span_count, status) VALUES (?,?,?,?)",
                (trace_id, trace.get("seed"), len(spans), status),
            )
            self.conn.executemany(
                """INSERT INTO spans(trace_id, span_id, parent_span_id, name, kind,
                       start_seq, end_seq, status, error_type, error_message,
                       attributes, input_ref, output_ref)
                   VALUES (:trace_id,:span_id,:parent_span_id,:name,:kind,
                       :start_seq,:end_seq,:status,:error_type,:error_message,
                       :attributes,:input_ref,:output_ref)""",
                [self._row(trace_id, s) for s in spans],
            )
        return trace_id

    @staticmethod
    def _row(trace_id: str, s: Dict[str, Any]) -> Dict[str, Any]:
        err = s.get("error") or {}
        return {
            "trace_id": trace_id,
            "span_id": s["span_id"],
            "parent_span_id": s.get("parent_span_id"),
            "name": s["name"],
            "kind": s["kind"],
            "start_seq": s["start_seq"],
            "end_seq": s.get("end_seq"),
            "status": s["status"],
            "error_type": err.get("type"),
            "error_message": err.get("message"),
            "attributes": _json(s.get("attributes")),
            "input_ref": _json(s.get("input_ref")),
            "output_ref": _json(s.get("output_ref")),
        }

    # --- indexed queries -----------------------------------------------------
    def get_trace(self, trace_id: str) -> Optional[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM traces WHERE trace_id=?", (trace_id,)
        ).fetchone()

    def failed_traces(self) -> List[sqlite3.Row]:
        # uses idx_traces_status
        return self.conn.execute(
            "SELECT * FROM traces WHERE status='error' ORDER BY trace_id"
        ).fetchall()

    def timeline(self, trace_id: str) -> List[sqlite3.Row]:
        # uses idx_spans_trace_start
        return self.conn.execute(
            "SELECT * FROM spans WHERE trace_id=? ORDER BY start_seq", (trace_id,)
        ).fetchall()

    def children(self, trace_id: str, parent_span_id: Optional[str]) -> List[sqlite3.Row]:
        # uses idx_spans_parent
        if parent_span_id is None:
            return self.conn.execute(
                "SELECT * FROM spans WHERE trace_id=? AND parent_span_id IS NULL "
                "ORDER BY start_seq", (trace_id,)
            ).fetchall()
        return self.conn.execute(
            "SELECT * FROM spans WHERE trace_id=? AND parent_span_id=? ORDER BY start_seq",
            (trace_id, parent_span_id),
        ).fetchall()

    def error_spans(self, trace_id: str) -> List[sqlite3.Row]:
        # uses idx_spans_status
        return self.conn.execute(
            "SELECT * FROM spans WHERE trace_id=? AND status='error' ORDER BY start_seq",
            (trace_id,),
        ).fetchall()

    def get_span(self, trace_id: str, span_id: str) -> Optional[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM spans WHERE trace_id=? AND span_id=?", (trace_id, span_id)
        ).fetchone()

    # --- introspection -------------------------------------------------------
    def query_plan(self, sql: str, params: tuple = ()) -> str:
        rows = self.conn.execute("EXPLAIN QUERY PLAN " + sql, params).fetchall()
        return "\n".join(r["detail"] for r in rows)

    # --- mutation (used by the deletion attack) ------------------------------
    def delete_span(self, trace_id: str, span_id: str) -> None:
        with self.conn:
            self.conn.execute(
                "DELETE FROM spans WHERE trace_id=? AND span_id=?", (trace_id, span_id)
            )

    def clear_field(self, trace_id: str, span_id: str, column: str) -> None:
        if column not in {"error_message", "error_type", "parent_span_id",
                          "attributes", "end_seq", "input_ref", "output_ref"}:
            raise ValueError(f"refusing to clear column {column!r}")
        with self.conn:
            self.conn.execute(
                f"UPDATE spans SET {column}=NULL WHERE trace_id=? AND span_id=?",
                (trace_id, span_id),
            )
