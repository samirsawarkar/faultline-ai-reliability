"""SQLite schema for the FAULTLINE trace store.

Two tables: one row per trace, one row per span. Every access pattern the
viewer and the reconstruction path need is backed by an index, so a stranger
reconstructing a run never triggers a full table scan:

  * timeline (order a trace by time)      -> idx_spans_trace_start
  * children of a span (walk the tree)    -> idx_spans_parent
  * find the failure(s) in a trace        -> idx_spans_status
  * list failed traces                    -> idx_traces_status

`status` on `traces` is derived at ingest (error if any span errored) so the
"which runs failed?" question is answered without touching the spans table.
"""

SCHEMA = """
CREATE TABLE IF NOT EXISTS traces (
    trace_id   TEXT PRIMARY KEY,
    seed       INTEGER,
    span_count INTEGER NOT NULL,
    status     TEXT NOT NULL          -- 'ok' | 'error'
);

CREATE TABLE IF NOT EXISTS spans (
    trace_id       TEXT NOT NULL,
    span_id        TEXT NOT NULL,
    parent_span_id TEXT,
    name           TEXT NOT NULL,
    kind           TEXT NOT NULL,     -- agent | model | tool
    start_seq      INTEGER NOT NULL,
    end_seq        INTEGER,
    status         TEXT NOT NULL,     -- unset | ok | error
    error_type     TEXT,
    error_message  TEXT,
    attributes     TEXT,              -- JSON
    input_ref      TEXT,              -- JSON PayloadRef
    output_ref     TEXT,              -- JSON PayloadRef
    PRIMARY KEY (trace_id, span_id)
);

CREATE INDEX IF NOT EXISTS idx_spans_trace_start ON spans(trace_id, start_seq);
CREATE INDEX IF NOT EXISTS idx_spans_parent      ON spans(trace_id, parent_span_id);
CREATE INDEX IF NOT EXISTS idx_spans_status      ON spans(trace_id, status);
CREATE INDEX IF NOT EXISTS idx_traces_status     ON traces(status);
"""
