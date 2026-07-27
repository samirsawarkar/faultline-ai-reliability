# CHECKPOINT-17 — subgroup analysis + measurement gate

**Mission.** Find where aggregate metrics hide failure by fault, severity and hop
count.

**Fail condition.** A subgroup contradicts the headline claim and is ignored. —
**Not triggered.**

## What was built

A subgroup analyzer + measurement gate over the project's evaluation data:

- **Slicing** by fault, severity, fault×severity, outcome (Day-15 detection) and by
  hop count (Day-7 reliability curve).
- **Discipline**: minimum sample size (n ≥ 5 to be reportable) and Holm-Bonferroni
  multiple-comparison correction on the reportable family.
- **Reversal detection** (Simpson's paradox), verified against a known kidney-stone
  paradox.
- **A measurement gate + audit** that recomputes the contradiction set and fails if
  any contradicting subgroup is unacknowledged.

11 tests gate it; three evidence artifacts prove it.

## Findings (dataset `de5068d574cae9fd`, n=44)

- **Headline:** overall detection accuracy 0.773.
- **Ordering reversal (Simpson):** aggregate deterministic 0.81 ≥ semantic 0.74,
  but **at severity 3 it reverses** — deterministic 0.0 (n=2, F2 latency below
  budget) vs semantic 0.667 (n=6). A confounded, under-powered reversal — surfaced.
- **Interval-excluding subgroups:** severity-1 faults (0.0) and the clean subgroup
  (1.0) both have intervals excluding the headline; low-severity F1/F2 are
  systematically missed.
- **Hop count:** the Day-7 "naive p^n overpredicts" headline **fails at hops 1–2**
  (first holds at hop 3).
- **After Holm correction, none of these is individually significant at n=44** —
  the spread is real but under-powered. That is the honest conclusion.

## The gate (fail condition, refused)

`evaluation_audit.json`: `no_contradiction_ignored = true`,
`reversal_detector_verified = true`, `discipline_applied = true`,
`audit_passed = true`. A test drops one acknowledged contradiction and shows the
audit flip to failed — a hidden subgroup cannot pass silently.

## Known limitations (committed, and on top of the findings doc)

Small n (most fault×severity cells are insufficient); the severity-3 reversal is
confounded and under-powered; detection and hop axes are separate populations, not
pooled; the "naive overpredicts" claim is hop-dependent; single dataset version.

## Mastery gate — all five

- **Explain** — `LEARN-simpson.md`: aggregation traps, Simpson's paradox, small-n and
  multiple-comparison traps.
- **Build** — `faultline_subgroups/`: slicer, gate, reversal detector, audit.
- **Debug** — `subgroup_report.json`: per-slice CIs and the reversal table.
- **Measure** — gated rates + Holm-corrected tests; the severity-3 reversal quantified.
- **Defend** — `evaluation_audit.json` + `DECISIONS.md` (D17-001…D17-007); no
  contradiction ignored, discipline applied, limitations committed.
