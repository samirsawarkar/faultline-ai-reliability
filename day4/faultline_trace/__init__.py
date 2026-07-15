"""FAULTLINE Day 4: linked spans that survive failures.

Public surface:
    Tracer(seed)                 -> tracer; one instance == one trace
    run_pipeline(tracer, task)   -> instrumented agent/model/tool demo
    audit_failed_trace(spans)    -> assert complete error span on failure
    audit_ok_trace(spans)        -> assert a clean success trace
    reference / redact / error_of -> redaction policy
"""
from .audit import IncompleteTraceError, audit_failed_trace, audit_ok_trace
from .pipeline import STEPS, RiskyToolError, run_pipeline
from .redaction import error_of, redact, reference
from .schema import (
    Span,
    SpanError,
    PayloadRef,
    is_complete,
    is_complete_error,
    validate_span,
)
from .tracer import Tracer

__all__ = [
    "Tracer",
    "run_pipeline",
    "STEPS",
    "RiskyToolError",
    "audit_failed_trace",
    "audit_ok_trace",
    "IncompleteTraceError",
    "Span",
    "SpanError",
    "PayloadRef",
    "is_complete",
    "is_complete_error",
    "validate_span",
    "reference",
    "redact",
    "error_of",
]
