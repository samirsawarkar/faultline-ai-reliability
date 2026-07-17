# DECISIONS.md — Day 8 (reproducible fault injection) decision log

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-07-18 · D8-001 · One uniform 10-field fault specification
**Decision.** Every fault is a frozen `FaultSpec` with exactly ten fields
(`fault_id, component, mode, severity, trigger, trigger_value, seed, rate,
label, spec_version`); `validate()` machine-checks the count and every field.
**Why.** A fault must be *data* — declarable, serializable, diffable, replayable
— not bespoke test code. A single shape makes faults composable and makes "what
was injected" a byte-exact artifact. The ten-field cap is a scope contract: a
fault that needs an eleventh field is out of scope for this injector.
**Reversal cost.** Adding a field is a schema change → bump `spec_version`
(invalidates old evidence by design; the version makes that visible).

### 2026-07-18 · D8-002 · Triggers are deterministic pure functions; "probabilistic" is seeded
**Decision.** `fires(spec, run_seed, seq, input_digest)` is pure. Three triggers
(`call_index`, `every_n`, `input_match`) ignore the seed entirely; the fourth
(`probabilistic`) draws from a `random.Random` seeded only from
`(spec.seed, run_seed, seq)`. Deterministic triggers must use `rate == 1.0`.
**Why.** The mission fails if triggers are non-deterministic. Reproducibility is
non-negotiable, but we still want a "some fraction fire" trigger for realism —
so we make it *seeded* (a fixed fraction fire; which ones is reproducible), the
exact opposite of chaos. Forbidding `rate != 1.0` on deterministic triggers stops
a fault from secretly being probabilistic.
**Reversal cost.** Low; add a trigger kind and its branch, keep purity.

### 2026-07-18 · D8-003 · Severity is an integer 1..5 on a fixed magnitude schedule
**Decision.** `severity` maps to a documented, deterministic magnitude per mode
(e.g. corrupt offset `= severity*111`; stall cost `= severity*10`; truncate keeps
`ceil(len*(1-0.15*severity))`, always dropping ≥1). No free-form magnitude field.
**Why.** "Severity" must mean the same thing on every machine and in every
replay. A bounded integer with a published schedule is auditable; a free-form
magnitude is not.
**Reversal cost.** Change the schedule → bump `spec_version` (changes evidence).

### 2026-07-18 · D8-004 · Ground truth is written at injection time, out of band
**Decision.** `GroundTruthLog` is populated from the *injection decision*, before
any output is produced, and is never returned to the caller. Every call gets
exactly one entry (`clean` or a fault label), contiguous by `seq`.
**Why.** The mission requires *independent* truth labels. If truth were derived
from the produced output, it wouldn't be independent — and a detector could
recover it. Writing from the decision, and keeping the log separate from the
output/trace, makes "did the detector find the fault?" a fair question.
**Reversal cost.** None; this is the deliverable's core.

### 2026-07-18 · D8-005 · Labels join the trace by span_id, never live inside a span
**Decision.** The boundary records a Day-4 span with only public
component/output; the truth entry stores that span's `span_id`. A labelled trace
is reconstructed by *joining* the log to the trace on `span_id`.
**Why.** "Ground-truth trace labels" must not mean "labels embedded in the
trace" — that would be leakage. Beside-the-sample labelling (like `y` kept out of
`X`) preserves both a labelled dataset and an honest observable surface.
**Reversal cost.** None; additive.

### 2026-07-18 · D8-006 · No-leakage is defined over the label namespace, not mode words
**Decision.** `leakage_scan` searches observable surfaces (outputs + trace) for
the ground-truth **labels and fault ids**, not the generic **mode words**
(`error`, `drop`, …). Labels use a reserved `fault:` prefix.
**Why.** A mode names a fault *kind* whose effect is often legitimately
observable (a raised error, an empty result) and collides with generic words
(a span's `status: "error"`). Leakage means the *answer key* — the label — is
readable from the sample, not that the fault had a visible effect. Scoping the
check to a reserved namespace makes it exact and non-vacuous (a planted label is
still caught; see `test_leakage_scan_would_catch_a_planted_leak`).
**Reversal cost.** Low; widen or narrow the needle set in one function.

### 2026-07-18 · D8-007 · A `stall` mode whose only effect is a side-channel cost
**Decision.** `stall` leaves output content byte-identical to clean and moves
only a separate `cost_units` meter.
**Why.** It is the cleanest possible proof of independent truth: a stalled call
and a clean call are indistinguishable by content, so *no function of the output
content can recover the label* — the truth must come from the log. It also keeps
the two observation channels (content vs cost) independent.
**Reversal cost.** None; it is one of six modes.

### 2026-07-18 · D8-008 · Wrap a generic call boundary, not the Day-7 chain
**Decision.** `InjectingChannel` wraps any object with
`call(component, payload) -> dict` (exactly Day 6's channel shape), demoed with a
stdlib `DemoChannel`.
**Why.** Fault injection should be reusable across every later day that injects
into the real baseline/agent, not welded to one experiment. The Day-6 channel
contract is already the seam the whole repo speaks.
**Reversal cost.** Low; an adapter can drive any specific subject through the
same `call` contract later.
