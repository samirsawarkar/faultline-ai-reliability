# REDACTION.md — what a span is allowed to remember (v1)

A tracer that records everything is a data-exfiltration tool. FAULTLINE's policy:
**spans store references, not payloads, and every stored string is scrubbed.**

## The two leaks this closes

1. **Raw payloads.** Prompts, tool arguments, and results routinely carry
   secrets. Spans never embed them; they store a `PayloadRef`
   (`sha256` + `size_bytes` + bounded `preview` + `redacted` flag), all computed
   from the *redacted* canonical form.
2. **Raw error text.** Exceptions interpolate secrets
   (`RuntimeError(f"auth failed token={t}")`). `error_of` masks the message
   before it becomes a `SpanError`, so failures are recorded without leaking.

## Rules

- **Sensitive keys** (dropped at any depth, value → `***REDACTED***`):
  `secret, password, passwd, token, api_key, apikey, authorization, auth, answer`.
  (`answer` is here on purpose: FAULTLINE answer tokens are the scored quantity —
  they must not sit in plaintext inside observability data.)
- **Sensitive substrings** (masked inside any string, incl. error messages):
  `key=value` forms for the sensitive keys, and `Bearer <token>`.
- **Preview** is capped at 120 chars of the redacted canonical JSON, then
  `...(truncated)`.
- The policy is **pure and deterministic**: same input → same `PayloadRef` and
  same masked message. This is what lets failed traces be reproducible evidence.

## Guarantee, and how it's tested

- `tests/test_redaction.py` — keys dropped, substrings masked, refs leak-free,
  preview bounded, error messages scrubbed.
- `tests/test_forced_failure.py::test_secret_never_leaks_in_failed_trace` and the
  100-run experiment both assert `hunter2` (the injected secret, threaded through
  payloads *and* the exception text) never appears in the serialized trace.

## Non-goals (v1)

- Not a substitute for not-collecting sensitive data upstream; it is defence in
  depth for the trace layer.
- No allow-list encryption / tokenization of payloads yet (only reference +
  preview). A payload store keyed by `sha256` is the natural next step.
