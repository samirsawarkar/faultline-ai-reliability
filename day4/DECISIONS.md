# DECISIONS.md — Day 4 (tracing) decision log

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-07-15 · D4-001 · A span is written at entry and closed in `finally`
**Decision.** `Tracer.span` appends the span to the trace before running the
body and sets `end_seq`/`status`/`error` in a `finally`.
**Why.** This is the whole mission: "a failure can occur without a complete
error span" must be impossible. If the span were written on *success* only, a
crash would leave no record; if closed outside `finally`, an exception could skip
the close. `finally` is the one construct that runs on every exit path.
**Reversal cost.** None desired — foundational.

### 2026-07-15 · D4-002 · No LLM; the model slot is a deterministic stub
**Decision.** Instrument an `agent → model → tool` pipeline where the model is a
stub, not a real API.
**Why.** The tracer must be agnostic to whether the callee is a model or a stub.
A real API would make "100 forced-failure runs" non-deterministic and conflate
network flakiness with tracer correctness. When a later mission puts a real model
in that slot, this tracer wraps it unchanged.
**Reversal cost.** Swap the stub for a client; spans need no change.

### 2026-07-15 · D4-003 · Logical clock, not wall clock
**Decision.** `start_seq`/`end_seq` are a monotonic counter.
**Why.** Byte-reproducible traces (stable committed evidence, deterministic
experiment) with strict ordering and duration. Wall-clock latency is a separate,
later concern.
**Reversal cost.** Add a real-time field alongside; no schema break.

### 2026-07-15 · D4-004 · Payload references, never raw payloads
**Decision.** Spans store `PayloadRef` (sha256 + size + bounded preview),
computed from the redacted form.
**Why.** Bounds trace size and makes leakage structurally hard: there is nowhere
in a span to put a raw payload.
**Reversal cost.** Adding a payload store keyed by sha256 is additive.

### 2026-07-15 · D4-005 · Redact keys AND substrings, including error messages
**Decision.** Drop sensitive keys at any depth; mask `key=value`/`Bearer` in
strings and in exception messages.
**Why.** The failure path is exactly where secrets leak (they get interpolated
into error text). Redacting only inputs would leave that hole open.
**Reversal cost.** Policy list is data; extend freely (v-bump if it changes
committed digests).

### 2026-07-15 · D4-006 · Audit encodes the fail condition as an assertion
**Decision.** `audit_failed_trace` requires: links intact, zero open spans, ≥1
complete error span, and error propagation from each error leaf to the root.
**Why.** "Complete error span" must be machine-checkable, not a vibe. The same
function guards the test and stamps the evidence report.
**Reversal cost.** None; additive.
