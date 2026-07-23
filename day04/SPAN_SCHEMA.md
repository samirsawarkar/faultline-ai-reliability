# SPAN_SCHEMA.md — the span record (v1)

A **span** is the durable record of one risky operation. It is written at the
moment the operation *begins* and closed in a `finally`, so a span exists — and
is complete — even when the operation crashes.

## Fields

| Field | Type | Meaning |
|---|---|---|
| `trace_id` | str | The run this span belongs to. One `Tracer` == one trace. |
| `span_id` | str | Unique within the trace. |
| `parent_span_id` | str \| null | Link to the enclosing operation; `null` for the root. |
| `name` | str | Operation name, e.g. `agent`, `model.plan`, `tool.sum`. |
| `kind` | enum | `agent` \| `model` \| `tool`. |
| `start_seq` | int | Logical clock at entry. **Always set.** |
| `end_seq` | int \| null | Logical clock at exit. `null` ⇒ span still open (a bug). |
| `status` | enum | `unset` \| `ok` \| `error`. |
| `error` | SpanError \| null | Present iff `status == error`. |
| `attributes` | map<str,str> | Small redacted key/values. |
| `input_ref` | PayloadRef \| null | Reference to the input payload. |
| `output_ref` | PayloadRef \| null | Reference to the output payload. |

**SpanError** = `{ type, message }` — `message` is already redacted.

**PayloadRef** = `{ sha256, size_bytes, preview, redacted }`. Payloads are never
embedded raw; every field is derived from the *redacted* canonical form, so a
span cannot leak a secret and is content-addressable. See [REDACTION.md](REDACTION.md).

## Why logical time, not wall clock

`start_seq`/`end_seq` are a monotonic counter, not `time.time()`. This makes
traces byte-reproducible (so the forced-failure experiment is deterministic and
the committed example traces are stable) while still giving strict ordering and
duration (`end_seq - start_seq`). Wall-clock timing is a later, orthogonal
concern.

## Completeness — the definitions the mission hinges on

- **complete** (`is_complete`): `start_seq` set, `end_seq` set, `end_seq ≥
  start_seq`, `status ∈ {ok, error}`.
- **complete error span** (`is_complete_error`): complete, `status == error`,
  and `error` carries a non-empty `type` and `message`.

**Fail condition (mission):** a failure that leaves *any* span open, or an error
span missing its `error`, or no error span at all. `audit_failed_trace` asserts
none of these can happen, over 100 forced-failure runs.

## Invariants (validated in `to_json`)

1. Required fields present; `kind`/`status` within their enums.
2. A span is never its own parent; every non-root `parent_span_id` resolves.
3. Exactly one root per trace.
4. `status == error` ⇒ `error` present.
