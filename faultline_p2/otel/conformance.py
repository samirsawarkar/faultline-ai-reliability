"""OpenTelemetry GenAI Semantic Conventions Conformance Validator."""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from typing import Any, Dict, List, Optional

from .models import OTelSpan, OTelTrace, SpanKind


@dataclass
class ConformanceViolation:
    """Represents a specific semantic convention or schema violation."""
    span_id: str
    span_name: str
    operation: str
    violation_type: str  # "missing_required", "name_drift", "type_mismatch", "invalid_nesting", "invalid_kind"
    message: str


@dataclass
class ConformanceReport:
    """Summary report of semantic conventions conformance evaluation."""
    semconv_version: str
    traces_evaluated: int
    spans_evaluated: int
    violations: List[ConformanceViolation] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "semconv_version": self.semconv_version,
            "traces_evaluated": self.traces_evaluated,
            "spans_evaluated": self.spans_evaluated,
            "passed": self.passed,
            "violation_count": len(self.violations),
            "violations": [
                {
                    "span_id": v.span_id,
                    "span_name": v.span_name,
                    "operation": v.operation,
                    "violation_type": v.violation_type,
                    "message": v.message,
                }
                for v in self.violations
            ],
        }


def load_pinned_semconv_registry(schema_filename: str = "semconv_v1_29_0.json") -> Dict[str, Any]:
    """Load the pinned OpenTelemetry GenAI semantic convention registry."""
    registry_dir = os.path.join(os.path.dirname(__file__), "registry")
    schema_path = os.path.join(registry_dir, schema_filename)
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Pinned semconv registry schema not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


class SemconvValidator:
    """Validates emitted OpenTelemetry spans against the pinned semantic conventions registry."""

    def __init__(self, registry: Optional[Dict[str, Any]] = None):
        self.registry = registry or load_pinned_semconv_registry()
        self.semconv_version = self.registry.get("semconv_version", "1.29.0")
        self.operations = self.registry.get("operations", {})
        self.attribute_types = self.registry.get("attribute_types", {})

    def validate_trace(self, trace: OTelTrace) -> ConformanceReport:
        """Validate an entire trace bundle for GenAI semantic conventions conformance."""
        violations: List[ConformanceViolation] = []
        span_map: Dict[str, OTelSpan] = {s.span_id: s for s in trace.spans}

        for span in trace.spans:
            parent_span = span_map.get(span.parent_span_id) if span.parent_span_id else None
            span_violations = self.validate_span(span, parent_span)
            violations.extend(span_violations)

        return ConformanceReport(
            semconv_version=self.semconv_version,
            traces_evaluated=1,
            spans_evaluated=len(trace.spans),
            violations=violations,
        )

    def validate_span(
        self, span: OTelSpan, parent_span: Optional[OTelSpan] = None
    ) -> List[ConformanceViolation]:
        """Validate a single span against the pinned semantic convention rules."""
        violations: List[ConformanceViolation] = []
        op_name = span.attributes.get("gen_ai.operation.name")

        # 1. Operation name presence and validity
        if not op_name:
            violations.append(
                ConformanceViolation(
                    span_id=span.span_id,
                    span_name=span.name,
                    operation="unknown",
                    violation_type="missing_required",
                    message="Missing required attribute 'gen_ai.operation.name'",
                )
            )
            return violations

        if op_name not in self.operations:
            violations.append(
                ConformanceViolation(
                    span_id=span.span_id,
                    span_name=span.name,
                    operation=str(op_name),
                    violation_type="name_drift",
                    message=f"Unknown gen_ai.operation.name '{op_name}'; not defined in semconv v{self.semconv_version}",
                )
            )
            return violations

        op_spec = self.operations[op_name]

        # 2. Span Kind validation
        kind_name = SpanKind(span.kind).name
        allowed_kinds = op_spec.get("allowed_span_kinds", [])
        if allowed_kinds and kind_name not in allowed_kinds:
            violations.append(
                ConformanceViolation(
                    span_id=span.span_id,
                    span_name=span.name,
                    operation=op_name,
                    violation_type="invalid_kind",
                    message=f"Span kind {kind_name} is not permitted for operation '{op_name}'. Allowed: {allowed_kinds}",
                )
            )

        # 3. Hierarchy and Nesting validation
        expected_parent_op = op_spec.get("parent_operation")
        if expected_parent_op is None:
            if span.parent_span_id is not None:
                violations.append(
                    ConformanceViolation(
                        span_id=span.span_id,
                        span_name=span.name,
                        operation=op_name,
                        violation_type="invalid_nesting",
                        message=f"Root operation '{op_name}' must not have a parent_span_id (got {span.parent_span_id})",
                    )
                )
        else:
            if parent_span is None:
                violations.append(
                    ConformanceViolation(
                        span_id=span.span_id,
                        span_name=span.name,
                        operation=op_name,
                        violation_type="invalid_nesting",
                        message=f"Operation '{op_name}' requires parent operation '{expected_parent_op}', but parent is missing",
                    )
                )
            else:
                parent_op = parent_span.attributes.get("gen_ai.operation.name")
                if parent_op != expected_parent_op:
                    violations.append(
                        ConformanceViolation(
                            span_id=span.span_id,
                            span_name=span.name,
                            operation=op_name,
                            violation_type="invalid_nesting",
                            message=f"Operation '{op_name}' requires parent operation '{expected_parent_op}', got '{parent_op}'",
                        )
                    )

        # 4. Required attributes presence
        required_attrs = op_spec.get("required_attributes", [])
        for req in required_attrs:
            if req not in span.attributes or span.attributes[req] is None or span.attributes[req] == "":
                violations.append(
                    ConformanceViolation(
                        span_id=span.span_id,
                        span_name=span.name,
                        operation=op_name,
                        violation_type="missing_required",
                        message=f"Operation '{op_name}' missing required attribute '{req}'",
                    )
                )

        # 5. Attribute Name Drift and Type Validation
        for attr_key, attr_val in span.attributes.items():
            if attr_key.startswith("gen_ai."):
                if attr_key not in self.attribute_types:
                    violations.append(
                        ConformanceViolation(
                            span_id=span.span_id,
                            span_name=span.name,
                            operation=op_name,
                            violation_type="name_drift",
                            message=f"Attribute name drift detected: '{attr_key}' is not a valid GenAI attribute in semconv v{self.semconv_version}",
                        )
                    )
                    continue

                type_spec = self.attribute_types[attr_key]
                expected_type = type_spec.get("type")
                if expected_type == "int":
                    if not isinstance(attr_val, int) or isinstance(attr_val, bool):
                        violations.append(
                            ConformanceViolation(
                                span_id=span.span_id,
                                span_name=span.name,
                                operation=op_name,
                                violation_type="type_mismatch",
                                message=f"Attribute '{attr_key}' must be int, got {type(attr_val).__name__} ({attr_val})",
                            )
                        )
                elif expected_type == "double":
                    if not isinstance(attr_val, (float, int)) or isinstance(attr_val, bool):
                        violations.append(
                            ConformanceViolation(
                                span_id=span.span_id,
                                span_name=span.name,
                                operation=op_name,
                                violation_type="type_mismatch",
                                message=f"Attribute '{attr_key}' must be double/float, got {type(attr_val).__name__} ({attr_val})",
                            )
                        )
                elif expected_type == "string":
                    if not isinstance(attr_val, str):
                        violations.append(
                            ConformanceViolation(
                                span_id=span.span_id,
                                span_name=span.name,
                                operation=op_name,
                                violation_type="type_mismatch",
                                message=f"Attribute '{attr_key}' must be string, got {type(attr_val).__name__} ({attr_val})",
                            )
                        )

                # Enum value validation
                allowed_enums = type_spec.get("enum")
                if allowed_enums and attr_val not in allowed_enums:
                    violations.append(
                        ConformanceViolation(
                            span_id=span.span_id,
                            span_name=span.name,
                            operation=op_name,
                            violation_type="name_drift",
                            message=f"Attribute '{attr_key}' value '{attr_val}' not in permitted enum {allowed_enums}",
                        )
                    )

        # 6. Timestamp validity
        if span.end_time_unix_nano < span.start_time_unix_nano:
            violations.append(
                ConformanceViolation(
                    span_id=span.span_id,
                    span_name=span.name,
                    operation=op_name,
                    violation_type="type_mismatch",
                    message=f"Span end_time ({span.end_time_unix_nano}) precedes start_time ({span.start_time_unix_nano})",
                )
            )

        return violations


def validate_trace_conformance(trace: OTelTrace) -> ConformanceReport:
    """Convenience helper to validate a trace against the pinned semconv registry."""
    validator = SemconvValidator()
    return validator.validate_trace(trace)
