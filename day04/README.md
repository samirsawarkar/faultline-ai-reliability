# FAULTLINE — Day 4: linked spans that survive failures

Record every risky operation in linked spans that survive failures.

> **Fail condition:** a failure can occur without a complete error span.
> **Status: not triggered** — 100/100 forced-failure runs leave complete error
> spans (`evidence/forced_failure_report.json`).

## What's here

```
faultline_trace/
  schema.py     Span / PayloadRef / SpanError; is_complete[_error]; validation
  tracer.py     Tracer: span() writes at entry, closes in finally (never leaks a span)
  redaction.py  redact keys + mask secrets (incl. error messages); leak-free PayloadRef
  pipeline.py   instrumented agent -> model -> tool demo with parent-child links
  audit.py      audit_failed_trace: the machine definition of "complete error span"
scripts/
  make_traces.py  writes the two example traces + the 100-run experiment report
tests/
  test_forced_failure.py  the gate: 100 mid-tool failures, all complete + no leaks
  test_tracer.py          links, determinism, always-closed spans
  test_redaction.py       policy behavior
  test_schema.py          validation + completeness predicates
evidence/
  trace_normal.json          one clean trace
  trace_failed.json          one failed trace (secret redacted, error propagated)
  forced_failure_report.json  audit of 100 forced-failure runs
SPAN_SCHEMA.md · REDACTION.md · DECISIONS.md · LEARN-otel.md · REFLECTION.md
```

## Quickstart

```
python -m pytest tests/ -v        # 19 tests: gate + schema + redaction + tracer
python scripts/make_traces.py     # regenerate evidence (deterministic)
```

Standard library only (developed on CPython 3.9). No LLM API — see REFLECTION.md.

## The guarantee, in one paragraph

Every span is appended to the trace the instant its operation begins, and its
end/status/error are written in a `finally`. So return, `raise`, or a child's
exception propagating through — the span is always closed, and a failing span is
always a *complete error span* with a redacted error. `audit_failed_trace`
asserts links are intact, no span is left open, and the error propagates from
each failing leaf up to the root. That audit runs green across 100 forced
failures with the injected secret never reaching the trace.

## Mastery map

- **Explain** → `LEARN-otel.md`, `SPAN_SCHEMA.md`
- **Build** → `faultline_trace/`
- **Debug** → complete-on-crash spans + `Tracer.open_spans()`
- **Measure** → `audit.py`, `evidence/forced_failure_report.json`
- **Defend** → `DECISIONS.md`
