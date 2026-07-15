# LEARN-otel.md — the OpenTelemetry span mental model

Notes from the core OTel tracing model, mapped to what we built.

## The model

- **Trace** = one end-to-end operation, a tree (really a DAG) of spans sharing a
  `trace_id`.
- **Span** = one unit of work: a name, a start and end time, a status, key/value
  **attributes**, timestamped **events**, and **links**. A span with no parent is
  the **root**.
- **Parent/child** = causal nesting. The child's `parent_span_id` is the span
  that was active when it started. OTel tracks "the active span" in **context**;
  starting a child reads that context, finishing restores it. Our `Tracer._stack`
  is exactly this context, specialized to one synchronous trace.
- **Status** = `Unset | Ok | Error`. Recording an exception sets `Error` and
  attaches exception info — precisely our `status="error"` + `SpanError`.
- **Span kind** — OTel uses `SERVER/CLIENT/INTERNAL/…`; we use a domain-specific
  `agent | model | tool`, which is the same idea (what *sort* of operation).

## Where our design maps

| OTel concept | Here |
|---|---|
| Trace / `trace_id` | `Tracer` instance / `trace_id` |
| Span start/end | `start_seq` / `end_seq` (logical, not wall clock) |
| Active-span context | `Tracer._stack` |
| `record_exception` + `set_status(Error)` | `except`: set `error` + `status` |
| Attributes | `attributes` (redacted) |
| Span processor / exporter | `to_json()` (+ evidence files) |

## The one idea we lean on hardest

OTel's guidance is that a span **must always be ended** — a leaked (never-ended)
span is a lost operation. The idiomatic pattern is start-in-a-context-manager,
end-in-`finally`, record-exception-on-error. Our mission's fail condition ("a
failure without a complete error span") *is* the "always end the span" rule made
into an enforced, tested invariant.

## Deliberate simplifications (and why they're safe)

- **Logical clock, not real time** — reproducibility now; wall-clock latency is
  additive later (D4-003).
- **Single synchronous trace per `Tracer`** — no cross-thread context
  propagation. Enough for a deterministic agent; OTel's `Context`/`contextvars`
  is the upgrade path when concurrency arrives.
- **Reference + redact instead of full payloads** — OTel leaves PII handling to
  the user; we bake it into the span layer (D4-004/005).
