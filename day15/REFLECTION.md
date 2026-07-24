# REFLECTION.md — five-minute mission reflection (Day 15)

**Mission.** Measure per-fault precision, recall and confusion against injection
truth.
**Fail condition.** False positives or false negatives are hidden by aggregate
metrics. — *Not triggered:* results are per class with intervals, a reconciliation
proves every FP/FN is listed (0 FP + 10 FN = 10 failures), and each miss carries a
Day-4 trace in `evidence/traces/`. See [CHECKPOINT-15.md](CHECKPOINT-15.md).

**Do we need an LLM API now? No.** Q2 measures the fixed, deterministic detectors
against the seeded oracle. Its output is precisely the map of where those detectors
fail — and the irreducible-escape half of that map is what *motivates* introducing a
judge in Mission 16, deployed only where deterministic detection provably cannot reach.

**The sharpest decision.** Classifying the false negatives (D15-004). "10 misses" is
a dead number; "4 irreducible semantic escapes + 6 threshold-reducible" is a
roadmap. It says: tune the schema range / latency budget for six of them, and build
semantic evaluation for the other four — and it names exactly which four.

**The honest caveat I kept in.** The per-class and group intervals are wide at n=44,
and the deterministic/semantic group bands overlap. I did not hide that behind the
clean point estimates. The split is *directional* at this sample size; what does not
depend on n is the structural fact (Days 10–11) that `drift_value` and
`context_drift` are byte-identical in form to correct outputs, so no threshold
catches them. That structural proof is the durable part of the finding.

**Mastery gate.**
- *Explain* — [LEARN-imbalanced-metrics.md](LEARN-imbalanced-metrics.md).
- *Build* — per-class confusion + Wilson CIs + det/sem groups + investigation.
- *Debug* — [`evidence/traces/`](evidence/traces): a trace per FP/FN.
- *Measure* — [`evidence/q2_results.json`](evidence/q2_results.json).
- *Defend* — [DECISIONS.md](DECISIONS.md), D15-001…D15-006.

**What I'd watch next.** Mission 16 validates a narrow LLM judge — the tool for the
four irreducible escapes Q2 just isolated; Mission 17 adds subgroup analysis + a
measurement gate; and a larger dataset would tighten these intervals so the group
split moves from directional to significant.
