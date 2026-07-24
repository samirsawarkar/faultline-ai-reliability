# DECISIONS.md — Day 15 (Q2: detection accuracy per fault) decision log

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-07-25 · D15-001 · Report per class first; the aggregate only to expose what it hides
**Decision.** The primary output is a per-fault confusion matrix. The micro
(pooled) and macro (mean-of-class) recalls are reported only in an
`aggregation_warning` that states they hide the spread.
**Why.** The fail condition is that FPs/FNs get hidden by aggregate metrics. Making
per-class the headline, and framing the aggregate as a cautionary artifact, meets
that head-on. The micro-vs-macro gap is itself the evidence of imbalance.
**Reversal cost.** None; per-class subsumes the aggregate.

### 2026-07-25 · D15-002 · Every FP/FN is reconciled and traced, not summarized
**Decision.** `no_hiding` asserts (failures listed == total FP + total FN), and
`collect_failures` attaches a Day-4 trace + observable + a `why` to every failing
sample.
**Why.** "Not hidden" has to be provable, not asserted. A reconciliation count plus
a per-example trace means a reviewer can enumerate and open every miss; there is no
class or example that the numbers quietly drop.
**Reversal cost.** None; it is the deliverable.

### 2026-07-25 · D15-003 · Wilson intervals on every rate (Day 14), reported even when wide
**Decision.** Recall and precision each carry a 95% Wilson interval; at n=44 (and
smaller per class) the bands are wide, and we report them as-is.
**Why.** A point recall without its interval invites over-reading a small sample.
The wide bands are honest: they say the per-class point estimates are directional,
and that the group comparison is not yet significant at this n — exactly the Day-14
lesson (overlap ≠ distinguishable).
**Reversal cost.** None; tighter bands come only from more data, not from hiding.

### 2026-07-25 · D15-004 · Classify false negatives: irreducible semantic escape vs threshold-reducible
**Decision.** An FN whose kind is `drift_value`/`offbase_tokens`/`context_drift` is
an irreducible semantic escape; any other miss is threshold-reducible.
**Why.** Not all misses are equal. Lumping them would hide the actionable
distinction: the threshold FNs are a budget/range choice (tighten and they vanish);
the semantic FNs cannot be closed by any deterministic detector and need a judge
(Mission 16). The taxonomy is the real Q2 finding.
**Reversal cost.** Low; the escape-kind set is one constant.

### 2026-07-25 · D15-005 · Evaluate the full labelled set for the headline; report the test split too
**Decision.** Because the detectors are fixed and untrained, the headline measures
the whole labelled set (n=44) for tighter intervals; the held-out test split is
reported alongside and agrees.
**Why.** There is nothing to overfit, so restricting to a held-out split only throws
away data and widens intervals for no leakage benefit (the Day-13 split matters when
*tuning/selecting*, which we are not). Reporting both keeps the held-out result
visible for anyone who wants it.
**Reversal cost.** None; both are in `q2_results.json`.

### 2026-07-25 · D15-006 · Reuse the exact Day-9/10/11 detectors via Day-13 predict
**Decision.** Q2 scores predictions from `faultline_eval.run_and_predict`, the same
path the dataset uses; `investigate.trace_sample` reproduces the same verdict and is
checked against it.
**Why.** The measurement must be of the detectors the project actually ships, not a
re-implementation. Sharing the prediction path guarantees the confusion matrix and
the traced examples describe the same behaviour.
**Reversal cost.** Low; a new detector is a new branch in the shared predict layer.
