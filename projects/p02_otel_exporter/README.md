# P02: OpenTelemetry GenAI Exporter & Conformance Testing

Exports FAULTLINE's internal SQLite `trace.db` into standardized OpenTelemetry GenAI spans conforming strictly to OpenTelemetry Semantic Conventions v1.29.0.

---

## Why This Exists

FAULTLINE records detailed execution telemetry in a local SQLite store (`trace.db`). To make this tracer legible to modern observability platforms, APMs, and reviewers, `faultline_p2/otel/` maps internal traces into standard OpenTelemetry GenAI semantic conventions.

Because many `gen_ai.*` semantic conventions carry Development stability status, a **conformance-tested** exporter ensures telemetry adheres to standard schemas without silent attribute drift or type degradation.

---

## Span Hierarchy & Structure

Each agent run emits a hierarchical trace tree:

```
invoke_agent (SpanKind.INTERNAL, root)
  └── chat (SpanKind.CLIENT)
        └── execute_tool (SpanKind.INTERNAL)
  └── chat (SpanKind.CLIENT)
        └── execute_tool (SpanKind.INTERNAL)
  └── chat (SpanKind.CLIENT, terminal answer)
```

- **`invoke_agent`**: Spans the entire multi-step task lifetime. Attributes: `gen_ai.operation.name="invoke_agent"`, `gen_ai.system`, `gen_ai.agent.name`, `gen_ai.agent.id`.
- **`chat`**: Spans each individual model generation step. Attributes: `gen_ai.operation.name="chat"`, `gen_ai.system`, `gen_ai.request.model`, `gen_ai.request.temperature`, `gen_ai.request.max_tokens`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`.
- **`execute_tool`**: Spans the execution of an authorized tool (`search`, `lookup`, `calc`). Nested directly under the requesting `chat` span. Attributes: `gen_ai.operation.name="execute_tool"`, `gen_ai.tool.name`, `gen_ai.system`.

---

## Conformance Testing (Pinned SemConv v1.29.0)

Conformance is not tested by asserting hardcoded strings in test assertions. Instead, the exporter is verified against a local hand transcription of the OpenTelemetry Semantic Conventions v1.29.0:
- **Registry Specification**: `faultline_p2/otel/registry/semconv_v1_29_0.json` (hand-transcribed from [open-telemetry/semantic-conventions/docs/gen-ai/gen-ai-spans.md](https://github.com/open-telemetry/semantic-conventions/blob/v1.29.0/docs/gen-ai/gen-ai-spans.md))
- **SemConv Version**: `1.29.0`
- **Schema URL**: `https://opentelemetry.io/schemas/1.29.0`
- **Validation Criteria**:
  1. Required attributes present for each operation (`gen_ai.operation.name`, `gen_ai.request.model`, `gen_ai.tool.name`).
  2. Span kinds strictly match allowed kinds for each operation.
  3. Strict parent-child nesting hierarchy (`invoke_agent` &#x2192; `chat` &#x2192; `execute_tool`).
  4. Attribute type safety (integers for tokens, doubles for temperature, strings for models).
  5. Zero attribute name drift: unknown or deprecated attributes (e.g. `gen_ai.prompt_tokens`) fail loudly.

---

## Sinks & Backend Transparency

- **SDK Availability**: `opentelemetry-sdk` is **not installed** in the pinned environment.
- **Specification Fidelity**: Rather than inventing a bespoke JSON shape, the exporter implements the standard OpenTelemetry OTLP HTTP/JSON specification (`resourceSpans` &#x2192; `scopeSpans` &#x2192; `spans` with AnyValue attribute formatting), verified via `jsonschema`.
- **Exercised Sinks**:
  - In-memory trace structures (`OTelTrace`, `OTelSpan`)
  - Standard OTLP JSON file export (`projects/p02_otel_exporter/otlp_traces.json`)
- **Unexercised Backends**:
  - Neither **Langfuse** nor **Arize Phoenix** was run live. Under FAULTLINE's zero-spend and offline discipline, we do not claim remote collector compatibility without live end-to-end integration receipts.

---

## Empirical Benchmark Findings

Driven by `projects/p02_otel_exporter/run.py` across multi-hop solver scenarios:
- **Traces Exported**: **350**
- **Total Spans**: **5,392**
  - `invoke_agent`: 350
  - `chat`: 2,696
  - `execute_tool`: 2,346
- **SemConv v1.29.0 Conformance**: **100.0% Passed (0 violations)**
- **Attribute Name Drift**: **0 violations**
- **OTLP JSON Schema Validation**: **100.0% Validated against OTLP Protobuf/JSON Schema**

---

## Reproduction

```bash
# Run the exporter benchmark
make p02

# Or directly:
.venv/bin/python projects/p02_otel_exporter/run.py --seed 42
```
