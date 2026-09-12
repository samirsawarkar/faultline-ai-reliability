"""Data models for OpenTelemetry GenAI Spans and Traces."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, List, Optional, Union


class SpanKind(IntEnum):
    """OpenTelemetry SpanKind values as specified in trace.proto."""
    SPAN_KIND_UNSPECIFIED = 0
    SPAN_KIND_INTERNAL = 1
    SPAN_KIND_SERVER = 2
    SPAN_KIND_CLIENT = 3
    SPAN_KIND_PRODUCER = 4
    SPAN_KIND_CONSUMER = 5


class StatusCode(IntEnum):
    """OpenTelemetry StatusCode values as specified in trace.proto."""
    STATUS_CODE_UNSET = 0
    STATUS_CODE_OK = 1
    STATUS_CODE_ERROR = 2


def format_otlp_attribute_value(val: Any) -> Dict[str, Any]:
    """Convert a native Python value into an OTLP AnyValue mapping."""
    if isinstance(val, bool):
        return {"boolValue": val}
    elif isinstance(val, int):
        return {"intValue": val}
    elif isinstance(val, float):
        return {"doubleValue": val}
    elif isinstance(val, str):
        return {"stringValue": val}
    elif isinstance(val, list):
        return {"arrayValue": {"values": [format_otlp_attribute_value(v) for v in val]}}
    elif isinstance(val, dict):
        return {
            "kvlistValue": {
                "values": [
                    {"key": k, "value": format_otlp_attribute_value(v)}
                    for k, v in val.items()
                ]
            }
        }
    return {"stringValue": str(val)}


@dataclass
class OTelSpan:
    """Represents an individual OpenTelemetry span."""
    trace_id: str
    span_id: str
    name: str
    kind: SpanKind
    start_time_unix_nano: int
    end_time_unix_nano: int
    parent_span_id: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    status_code: StatusCode = StatusCode.STATUS_CODE_OK
    status_message: Optional[str] = None

    def to_otlp_dict(self) -> Dict[str, Any]:
        """Convert to standard OTLP HTTP/JSON Span representation."""
        attrs = [
            {"key": k, "value": format_otlp_attribute_value(v)}
            for k, v in self.attributes.items()
        ]
        res: Dict[str, Any] = {
            "traceId": self.trace_id,
            "spanId": self.span_id,
            "name": self.name,
            "kind": int(self.kind),
            "startTimeUnixNano": str(self.start_time_unix_nano),
            "endTimeUnixNano": str(self.end_time_unix_nano),
            "attributes": attrs,
            "status": {
                "code": int(self.status_code),
            },
        }
        if self.parent_span_id:
            res["parentSpanId"] = self.parent_span_id
        if self.status_message:
            res["status"]["message"] = self.status_message
        return res


@dataclass
class OTelTrace:
    """A complete trace bundle representing an agent run and its child operations."""
    trace_id: str
    run_id: str
    spans: List[OTelSpan] = field(default_factory=list)

    @property
    def root_span(self) -> Optional[OTelSpan]:
        """Return the root span (parent_span_id is None)."""
        for s in self.spans:
            if s.parent_span_id is None:
                return s
        return None

    def get_children(self, span_id: str) -> List[OTelSpan]:
        """Return all direct child spans of the given span."""
        return [s for s in self.spans if s.parent_span_id == span_id]

    def to_otlp_resource_spans(
        self,
        service_name: str = "faultline-agent",
        service_version: str = "0.1.0",
        schema_url: str = "https://opentelemetry.io/schemas/1.29.0",
    ) -> Dict[str, Any]:
        """Convert the trace to standard OTLP ResourceSpans dictionary."""
        return {
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": service_name}},
                    {"key": "service.version", "value": {"stringValue": service_version}},
                ]
            },
            "scopeSpans": [
                {
                    "scope": {
                        "name": "faultline.otel.exporter",
                        "version": "1.29.0",
                    },
                    "spans": [s.to_otlp_dict() for s in self.spans],
                    "schemaUrl": schema_url,
                }
            ],
            "schemaUrl": schema_url,
        }
