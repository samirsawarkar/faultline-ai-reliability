"""OpenTelemetry GenAI Exporter reading trace.db and emitting compliant spans."""
from __future__ import annotations

import datetime
import hashlib
import json
import sqlite3
from typing import Any, Dict, List, Optional, Union

from .models import (
    OTelSpan,
    OTelTrace,
    SpanKind,
    StatusCode,
)


def _iso_to_unix_nano(iso_str: Optional[str], default_offset_s: float = 0.0) -> int:
    """Convert an ISO-8601 timestamp string to integer nanoseconds."""
    if not iso_str:
        now = datetime.datetime.now(datetime.timezone.utc).timestamp() + default_offset_s
        return int(now * 1_000_000_000)
    try:
        dt = datetime.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return int(dt.timestamp() * 1_000_000_000)
    except Exception:
        now = datetime.datetime.now(datetime.timezone.utc).timestamp() + default_offset_s
        return int(now * 1_000_000_000)


def _derive_trace_id(run_id: str) -> str:
    """Derive deterministic 32-hex-character W3C trace ID from run_id."""
    return hashlib.md5(f"faultline:trace:{run_id}".encode("utf-8")).hexdigest()


def _derive_span_id(key: str) -> str:
    """Derive deterministic 16-hex-character W3C span ID from a unique key."""
    return hashlib.md5(key.encode("utf-8")).hexdigest()[:16]


class OTelExporter:
    """Reads FAULTLINE trace.db and emits OpenTelemetry GenAI spans."""

    def __init__(self, db_path_or_conn: Union[str, sqlite3.Connection]):
        if isinstance(db_path_or_conn, str):
            self.conn = sqlite3.connect(db_path_or_conn)
        else:
            self.conn = db_path_or_conn
        self.conn.row_factory = sqlite3.Row

    def export_all_runs(self) -> List[OTelTrace]:
        """Export all runs from trace.db to OpenTelemetry traces."""
        cursor = self.conn.execute("SELECT run_id FROM runs ORDER BY start_time ASC")
        rows = cursor.fetchall()
        # If runs table empty, discover runs from spans table
        if not rows:
            cursor = self.conn.execute("SELECT DISTINCT run_id FROM spans ORDER BY run_id ASC")
            rows = cursor.fetchall()
        run_ids = [r["run_id"] for r in rows if r["run_id"]]
        return [self.export_run(rid) for rid in run_ids]

    def export_run(self, run_id: str) -> OTelTrace:
        """Export a single agent run into a hierarchical OTelTrace."""
        trace_id = _derive_trace_id(run_id)

        # 1. Fetch Run Metadata
        run_row = self.conn.execute(
            "SELECT * FROM runs WHERE run_id = ?", (run_id,)
        ).fetchone()

        # 2. Fetch All Step Spans
        spans_cursor = self.conn.execute(
            """
            SELECT * FROM spans 
            WHERE run_id = ? 
            ORDER BY step_index ASC, timestamp ASC
            """,
            (run_id,)
        )
        span_rows = spans_cursor.fetchall()

        # Determine timestamps for root invoke_agent span
        if run_row and run_row["start_time"]:
            run_start_nano = _iso_to_unix_nano(run_row["start_time"])
        elif span_rows and span_rows[0]["timestamp"]:
            run_start_nano = _iso_to_unix_nano(span_rows[0]["timestamp"]) - int(
                (span_rows[0]["latency_ms"] or 10.0) * 1_000_000
            )
        else:
            run_start_nano = _iso_to_unix_nano(None)

        if run_row and run_row["end_time"]:
            run_end_nano = _iso_to_unix_nano(run_row["end_time"])
        elif span_rows and span_rows[-1]["timestamp"]:
            run_end_nano = _iso_to_unix_nano(span_rows[-1]["timestamp"]) + 5_000_000
        else:
            run_end_nano = run_start_nano + 100_000_000

        if run_end_nano <= run_start_nano:
            run_end_nano = run_start_nano + 50_000_000

        # Provider and model for root span
        provider = "local"
        agent_id = run_id
        if span_rows:
            provider = span_rows[0]["provider"] or "local"
            if span_rows[0]["scenario_id"]:
                agent_id = span_rows[0]["scenario_id"]

        root_span_id = _derive_span_id(f"root:{run_id}")
        root_span = OTelSpan(
            trace_id=trace_id,
            span_id=root_span_id,
            parent_span_id=None,
            name="invoke_agent",
            kind=SpanKind.SPAN_KIND_INTERNAL,
            start_time_unix_nano=run_start_nano,
            end_time_unix_nano=run_end_nano,
            attributes={
                "gen_ai.operation.name": "invoke_agent",
                "gen_ai.system": provider,
                "gen_ai.agent.id": agent_id,
                "gen_ai.agent.name": "faultline-agent",
            },
            status_code=StatusCode.STATUS_CODE_OK,
        )

        all_spans: List[OTelSpan] = [root_span]

        # 3. Build Nested Spans: invoke_agent -> chat -> execute_tool
        for row in span_rows:
            step_idx = row["step_index"]
            step_ts_nano = _iso_to_unix_nano(row["timestamp"])
            latency_ms = float(row["latency_ms"] or 10.0)
            latency_nano = int(latency_ms * 1_000_000)

            chat_start_nano = max(run_start_nano, step_ts_nano - latency_nano)
            chat_end_nano = max(chat_start_nano + 1_000_000, step_ts_nano)

            model_name = row["model_name"] or "stub"
            row_provider = row["provider"] or provider
            prompt_tokens = int(row["prompt_tokens"] or 0)
            completion_tokens = int(row["completion_tokens"] or 0)

            chat_span_id = _derive_span_id(f"chat:{run_id}:{step_idx}:{row['span_id']}")
            chat_span = OTelSpan(
                trace_id=trace_id,
                span_id=chat_span_id,
                parent_span_id=root_span_id,
                name=f"chat {model_name}",
                kind=SpanKind.SPAN_KIND_CLIENT,
                start_time_unix_nano=chat_start_nano,
                end_time_unix_nano=chat_end_nano,
                attributes={
                    "gen_ai.operation.name": "chat",
                    "gen_ai.system": row_provider,
                    "gen_ai.request.model": model_name,
                    "gen_ai.request.temperature": 0.0,
                    "gen_ai.request.max_tokens": 4096,
                    "gen_ai.usage.input_tokens": prompt_tokens,
                    "gen_ai.usage.output_tokens": completion_tokens,
                },
                status_code=StatusCode.STATUS_CODE_OK,
            )
            all_spans.append(chat_span)

            # Check if this step executed a tool (search, lookup, calc)
            tool_name = row["tool_name"]
            if tool_name and tool_name not in ("answer", "none", "unknown"):
                tool_start_nano = chat_end_nano
                tool_end_nano = tool_start_nano + 2_000_000  # 2ms tool duration
                if tool_end_nano > run_end_nano:
                    run_end_nano = tool_end_nano + 1_000_000
                    root_span.end_time_unix_nano = run_end_nano

                tool_span_id = _derive_span_id(f"tool:{run_id}:{step_idx}:{tool_name}")
                tool_span = OTelSpan(
                    trace_id=trace_id,
                    span_id=tool_span_id,
                    parent_span_id=chat_span_id,
                    name=f"execute_tool {tool_name}",
                    kind=SpanKind.SPAN_KIND_INTERNAL,
                    start_time_unix_nano=tool_start_nano,
                    end_time_unix_nano=tool_end_nano,
                    attributes={
                        "gen_ai.operation.name": "execute_tool",
                        "gen_ai.tool.name": tool_name,
                        "gen_ai.system": row_provider,
                    },
                    status_code=StatusCode.STATUS_CODE_OK,
                )
                all_spans.append(tool_span)

        return OTelTrace(trace_id=trace_id, run_id=run_id, spans=all_spans)

    def to_otlp_json(
        self,
        traces: List[OTelTrace],
        service_name: str = "faultline-agent",
        service_version: str = "0.1.0",
    ) -> str:
        """Serialize traces to standard OTLP HTTP/JSON export payload string."""
        payload = self.to_otlp_dict(traces, service_name, service_version)
        return json.dumps(payload, indent=2)

    def to_otlp_dict(
        self,
        traces: List[OTelTrace],
        service_name: str = "faultline-agent",
        service_version: str = "0.1.0",
    ) -> Dict[str, Any]:
        """Serialize traces to standard OTLP HTTP/JSON export payload dictionary."""
        resource_spans = [
            t.to_otlp_resource_spans(service_name, service_version)
            for t in traces
        ]
        return {"resourceSpans": resource_spans}
