# REFLECTION.md — five-minute mission reflection (Day 10)

**Mission.** Separate schema-valid wrong data from explicit provider errors.
**Fail condition.** Schema-valid semantic corruption is treated as detected
without evidence. — *Not triggered:* the two escaping kinds are classified `OK`,
counted as false negatives, and shipped in `false_negatives.json` with the
oracle's expected-vs-got diff proving each is wrong. See [CHECKPOINT-10.md](CHECKPOINT-10.md).

**Do we need an LLM API now? No.** F3/F4 are about the *contract layer* — schema,
semantic invariants, explicit errors, and the boundary between them. All of that
is deterministic and cheap. The correctness oracle here is the clean channel; when
a real subject and a validated judge arrive (Mission 16), they slot into the same
truth/scoring seam without touching the detectors.

**The sharpest decision.** Keeping the semantic invariant deliberately partial
(D10-003). It would have been easy to tighten "value is a round ten" into the full
oracle and post a 1.0 recall — and meaningless. The honest move is a partial
invariant, a measured escape set, and oracle evidence for every miss. A missed
detection with proof beats a green number with none.

**The finding I didn't expect to be so clean.** Escape is *severity-invariant*.
Day 9 trained the intuition that bigger faults are easier to catch; here the
opposite holds for schema-valid corruption — a value that is 10x wrong is as
invisible as one that is 1% wrong, because both are legal values. That inversion
is the whole reason the quiet faults are the dangerous ones.

**Mastery gate.**
- *Explain* — [LEARN-semantic-invariants.md](LEARN-semantic-invariants.md).
- *Build* — oracle, five F3 corruptions, provider errors, mixed classifier, breaker.
- *Debug* — [`trace_f3_mixed.json`](evidence/trace_f3_mixed.json): per-call verdict
  vs oracle.
- *Measure* — [`contract_report.json`](evidence/contract_report.json) +
  [`false_negatives.json`](evidence/false_negatives.json).
- *Defend* — [DECISIONS.md](DECISIONS.md), D10-001…D10-007.

**What I'd watch next.** F5/F6 (Mission 11) — context corruption and loop
exhaustion — add families whose truth is stateful, not per-call; then Mission 13's
evaluation harness turns these confusion matrices into a versioned dataset, and
Mission 15 (Q2) reports detection accuracy with intervals across all six families.
