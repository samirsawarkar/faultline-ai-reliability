"""OpenTelemetry GenAI Semantic Conventions Conformance Tests.

Validates:
1. Emitted spans conform strictly to OpenTelemetry GenAI Semantic Conventions (pinned v1.29.0).
2. Hierarchy and nesting: invoke_agent (root) -> chat (client) -> execute_tool (internal).
3. Attribute presence, exact naming, and type safety (zero name drift).
4. OTLP HTTP/JSON serialization matches official OpenTelemetry protobuf/JSON shape.
5. Negative tests: attribute drift, type mismatch, and invalid nesting fail loudly.
"""
import json
import sqlite3
import pytest
import jsonschema

from faultline_p2.agent.agent import run_agent
from faultline_p2.agent.contracts import ScenarioTask, OutcomeStatus
from faultline_p2.agent.model import StubModel
from faultline_p2.env.corpus import build_corpus
from faultline_p2.trace.store import TraceStore
from faultline_p2.otel import (
    OTelExporter,
    OTelSpan,
    OTelTrace,
    SpanKind,
    StatusCode,
    SemconvValidator,
    validate_trace_conformance,
    load_pinned_semconv_registry,
)


def _create_real_agent_trace() -> OTelTrace:
    """Run a real multi-step scenario with TraceStore and export to OTelTrace."""
    corpus = build_corpus()
    store = TraceStore(":memory:")
    run_id = store.start_run()
    model = StubModel(behavior="solver")
    env = {"documents": corpus.documents}

    task = ScenarioTask(
        task_id=corpus.scenarios[0].scenario_id,
        prompt=corpus.scenarios[0].prompt,
        tier=corpus.scenarios[0].tier,
    )

    outcome = run_agent(task, env, model, step_cap=12, trace_store=store, run_id=run_id)
    store.end_run(run_id, "completed")

    assert outcome.status == OutcomeStatus.ANSWERED
    exporter = OTelExporter(store.conn)
    trace = exporter.export_run(run_id)
    store.close()
    return trace


def test_otel_exporter_from_real_agent_run():
    """Verify OTelExporter parses real SQLite trace and emits valid OTelTrace."""
    trace = _create_real_agent_trace()
    assert trace.trace_id is not None and len(trace.trace_id) == 32
    assert trace.root_span is not None
    assert trace.root_span.name == "invoke_agent"
    assert len(trace.spans) >= 3  # Root + at least 1 chat + at least 1 tool


def test_conformance_against_pinned_v1_29_0_registry():
    """Conformance Test: Emitted trace validates 100% against pinned semconv v1.29.0.

    Does not hand-write attribute names: dynamically evaluates against semconv_v1_29_0.json.
    """
    trace = _create_real_agent_trace()
    registry = load_pinned_semconv_registry("semconv_v1_29_0.json")
    assert registry["semconv_version"] == "1.29.0"

    validator = SemconvValidator(registry=registry)
    report = validator.validate_trace(trace)

    # Conformance must pass with zero violations
    assert report.passed, f"Semantic convention violations found: {report.to_dict()}"
    assert len(report.violations) == 0
    assert report.spans_evaluated >= 3


def test_nesting_hierarchy_and_span_kinds():
    """Verify strict hierarchy: invoke_agent (root) -> chat -> execute_tool."""
    trace = _create_real_agent_trace()
    root = trace.root_span
    assert root is not None
    assert root.parent_span_id is None
    assert root.kind == SpanKind.SPAN_KIND_INTERNAL
    assert root.attributes["gen_ai.operation.name"] == "invoke_agent"

    chat_spans = [s for s in trace.spans if s.attributes.get("gen_ai.operation.name") == "chat"]
    tool_spans = [s for s in trace.spans if s.attributes.get("gen_ai.operation.name") == "execute_tool"]

    assert len(chat_spans) >= 1
    assert len(tool_spans) >= 1

    # Every chat span must be direct child of root invoke_agent
    for chat in chat_spans:
        assert chat.parent_span_id == root.span_id
        assert chat.kind == SpanKind.SPAN_KIND_CLIENT
        assert "gen_ai.request.model" in chat.attributes
        assert isinstance(chat.attributes["gen_ai.request.model"], str)
        assert isinstance(chat.attributes["gen_ai.usage.input_tokens"], int)
        assert isinstance(chat.attributes["gen_ai.usage.output_tokens"], int)

    # Every execute_tool span must be direct child of its chat span
    chat_span_ids = {c.span_id for c in chat_spans}
    for tool in tool_spans:
        assert tool.parent_span_id in chat_span_ids
        assert tool.kind == SpanKind.SPAN_KIND_INTERNAL
        assert "gen_ai.tool.name" in tool.attributes
        assert isinstance(tool.attributes["gen_ai.tool.name"], str)


def test_attribute_name_drift_fails_loudly():
    """Verify validator catches and fails loudly on attribute name drift.

    If an exporter uses 'gen_ai.prompt_tokens' instead of 'gen_ai.usage.input_tokens',
    the validator MUST report a name_drift violation.
    """
    trace = _create_real_agent_trace()
    # Introduce deliberate name drift
    chat_span = next(s for s in trace.spans if s.attributes.get("gen_ai.operation.name") == "chat")
    chat_span.attributes["gen_ai.prompt_tokens"] = 42  # Deprecated / drifted name

    validator = SemconvValidator()
    report = validator.validate_trace(trace)

    assert not report.passed
    drift_violations = [v for v in report.violations if v.violation_type == "name_drift"]
    assert len(drift_violations) >= 1
    assert any("gen_ai.prompt_tokens" in v.message for v in drift_violations)


def test_attribute_type_mismatch_fails_loudly():
    """Verify validator catches type mismatches (e.g. string tokens instead of int)."""
    trace = _create_real_agent_trace()
    chat_span = next(s for s in trace.spans if s.attributes.get("gen_ai.operation.name") == "chat")
    chat_span.attributes["gen_ai.usage.input_tokens"] = "150"  # Invalid string instead of int

    validator = SemconvValidator()
    report = validator.validate_trace(trace)

    assert not report.passed
    type_violations = [v for v in report.violations if v.violation_type == "type_mismatch"]
    assert len(type_violations) >= 1
    assert any("input_tokens" in v.message for v in type_violations)


def test_invalid_nesting_fails_loudly():
    """Verify validator catches broken parent-child hierarchy."""
    trace = _create_real_agent_trace()
    tool_span = next(s for s in trace.spans if s.attributes.get("gen_ai.operation.name") == "execute_tool")
    tool_span.parent_span_id = None  # Orphaned execute_tool without parent chat span

    validator = SemconvValidator()
    report = validator.validate_trace(trace)

    assert not report.passed
    nesting_violations = [v for v in report.violations if v.violation_type == "invalid_nesting"]
    assert len(nesting_violations) >= 1


def test_otlp_json_schema_validation():
    """E3 Sink Test: Validate exported OTLP JSON matches standard protobuf/JSON schema.

    Verifies OTLP structure using jsonschema.
    """
    trace = _create_real_agent_trace()
    exporter = OTelExporter(sqlite3.connect(":memory:"))
    otlp_dict = exporter.to_otlp_dict([trace])
    otlp_json = exporter.to_otlp_json([trace])

    assert isinstance(otlp_json, str)
    parsed = json.loads(otlp_json)

    # Define standard OTLP HTTP/JSON trace export schema
    otlp_schema = {
        "type": "object",
        "required": ["resourceSpans"],
        "properties": {
            "resourceSpans": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["resource", "scopeSpans"],
                    "properties": {
                        "resource": {
                            "type": "object",
                            "required": ["attributes"],
                            "properties": {
                                "attributes": {"type": "array"}
                            }
                        },
                        "scopeSpans": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["scope", "spans"],
                                "properties": {
                                    "scope": {
                                        "type": "object",
                                        "required": ["name", "version"]
                                    },
                                    "spans": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "required": [
                                                "traceId", "spanId", "name", "kind",
                                                "startTimeUnixNano", "endTimeUnixNano",
                                                "attributes", "status"
                                            ],
                                            "properties": {
                                                "traceId": {"type": "string", "minLength": 32, "maxLength": 32},
                                                "spanId": {"type": "string", "minLength": 16, "maxLength": 16},
                                                "name": {"type": "string"},
                                                "kind": {"type": "integer"},
                                                "startTimeUnixNano": {"type": "string"},
                                                "endTimeUnixNano": {"type": "string"},
                                                "attributes": {"type": "array"},
                                                "status": {"type": "object", "required": ["code"]}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    # Validate against standard OTLP JSON schema
    jsonschema.validate(instance=parsed, schema=otlp_schema)

    # Check resource attributes
    res_attrs = parsed["resourceSpans"][0]["resource"]["attributes"]
    service_name = next(a["value"]["stringValue"] for a in res_attrs if a["key"] == "service.name")
    assert service_name == "faultline-agent"
