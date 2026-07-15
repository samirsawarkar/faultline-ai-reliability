# REFLECTION.md — five-minute mission reflection

**Mission.** Record every risky operation in linked spans that survive failures.
**Fail condition.** A failure can occur without a complete error span. — *Not
triggered:* 100/100 forced-failure runs left complete error spans, zero open
spans, zero secret leaks (`evidence/forced_failure_report.json`).

**Do we need an LLM API now? No.** This is observability, not intelligence. The
model slot is a deterministic stub so the tracer stays agnostic and the 100-run
experiment stays reproducible. A real model plugs into the same slot later
without touching the tracer (D4-002).

**Mastery gate.**
- *Explain* — [LEARN-otel.md](LEARN-otel.md): trace/span/context/status, and why
  "always end the span" is the core rule.
- *Build* — [faultline_trace/](faultline_trace/): schema, tracer, redaction,
  audit, instrumented pipeline.
- *Debug* — spans written at entry + closed in `finally` means a crash leaves a
  full record to debug from; `open_spans()` surfaces any leak.
- *Measure* — `is_complete_error` + `audit_failed_trace` make "complete error
  span" a machine check, stamped over 100 runs.
- *Defend* — [DECISIONS.md](DECISIONS.md): every choice, its why, its reversal
  cost.

**What I'd watch next.** Concurrency (contextvars instead of a list stack),
real-time latency alongside the logical clock, and a sha256-keyed payload store
so references can be rehydrated under access control.

**One honest limitation.** The tracer assumes one synchronous trace per `Tracer`
instance; it is not yet thread/async-safe. Fine for the deterministic agent,
called out so it isn't mistaken for done.
