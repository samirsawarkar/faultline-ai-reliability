# DECISIONS.md — Day 9 (F1/F2 detectors + scoring) decision log

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-07-19 · D9-001 · Detection and scoring are strictly separated
**Decision.** A detector (`detectors.py`) sees only the observable stream
(output or duration) and emits a signal; the scorer (`score.py`) is the ONLY code
that reads the Day-8 `GroundTruthLog`. A detector never sees truth.
**Why.** The mission fails if scores are computed against anything but injection
truth. Keeping the truth log out of the detector's reach makes "did it detect?"
un-gameable by construction — the same discipline as Day 8's out-of-band labels.
**Reversal cost.** None; this separation is the deliverable.

### 2026-07-19 · D9-002 · Scoring is a confusion matrix joined to truth by seq
**Decision.** `score(predicted_positive, truth, truth_positive)` aligns detector
positives to truth entries per `seq`, and raises if the detector flags a seq
absent from truth or if the truth log is not a complete, contiguous 0..n-1
labelling.
**Why.** A precision/recall number is only meaningful if every prediction is
matched to a real label. The alignment guard turns "scored against truth" from a
claim into an enforced precondition.
**Reversal cost.** Low; the join key could become `span_id` instead of `seq`.

### 2026-07-19 · D9-003 · The F1 detector is a schema validator, not an oracle
**Decision.** F1 detection checks structural well-formedness (types, value range,
token count and order), never correctness. The value range `[10, 150]` leaves
headroom so a small corruption is in-range and *passes*.
**Why.** Schema validation is the cheap, deterministic first line of defense a
real system actually has; conflating it with correctness would overstate what
validation buys you. The deliberate headroom produces an honest recall curve
(gross corruption caught, plausible corruption missed) instead of a vacuous 1.0.
**Reversal cost.** Tightening the schema raises recall but narrows what counts as
"valid"; it's a one-constant change (`VALUE_MAX`) that changes the sweep numbers.

### 2026-07-19 · D9-004 · Latency is virtual (cost units), never wall-clock
**Decision.** `duration = BASE_LATENCY + injected`, where `injected` is the Day-8
`stall` cost delta read off the channel meter. No real timer anywhere.
**Why.** A wall clock would make traces non-reproducible and conflate host jitter
with the fault under study — the same reason Days 4–7 use a logical clock. Virtual
latency still poses a real budget problem, which is all the detector needs.
**Reversal cost.** Swap in a measured clock at a real boundary later; the budget
detector and scorer are unchanged.

### 2026-07-19 · D9-005 · F2 detection is budget-gated, and the budget is explicit
**Decision.** The duration detector trips only when `duration > budget`; the
default budget (45) is a named constant and a swept parameter
(`f2_budget_sensitivity`).
**Why.** There is no absolute "too slow" — only "slower than the budget." Making
the budget explicit (and sweeping it) shows detection is a policy choice, not a
property of the fault, which is the Learn block's point about latency budgets.
**Reversal cost.** None; the budget is a parameter.

### 2026-07-19 · D9-006 · F1/F2 are named families built on Day-8, not a fork
**Decision.** `f1_corruption_spec` / `f2_latency_spec` are thin builders over the
Day-8 `FaultSpec`; F1 uses the content modes, F2 uses `stall`. Truth labels carry
`F1:` / `F2:` prefixes so the scorer can partition truth by family.
**Why.** The arc is cumulative: Day 9 should measure Day 8's injector, not
reimplement it. Prefixed labels let one run be scored per family without the
detector or scorer knowing anything extra.
**Reversal cost.** None; new families are new builders + a label prefix.

### 2026-07-19 · D9-007 · A specificity cross-check ships as evidence
**Decision.** Score the schema detector against latency truth and the duration
detector against corruption truth; assert both get recall 0.
**Why.** It proves the detectors are family-specific and that the scorer really
partitions truth by family — a guard against a detector accidentally scoring well
on the wrong labels. Also a concrete reminder that a green precision/recall means
nothing without the right truth.
**Reversal cost.** None; additive evidence.
