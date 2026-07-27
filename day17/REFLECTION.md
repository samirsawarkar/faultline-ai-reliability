# REFLECTION.md — five-minute mission reflection (Day 17)

**Mission.** Find where aggregate metrics hide failure by fault, severity and hop
count.
**Fail condition.** A subgroup contradicts the headline claim and is ignored. —
*Not triggered:* every interval-excluding subgroup and every ordering reversal is
surfaced and acknowledged, and the audit independently recomputes the contradiction
set and fails if any is dropped. See [CHECKPOINT-17.md](CHECKPOINT-17.md).

**Do we need an LLM API now? No.** This is an analysis-of-existing-results mission:
slice the Day-15 detection outcomes and the Day-7 hop curve, apply statistical
discipline, and gate the conclusions. Deterministic throughout.

**The sharpest decision.** Defining "contradiction" as *the interval excludes the
headline*, not *the point estimate differs* (D17-001). Point estimates always
differ; treating that as contradiction floods the report with 30 non-findings and
hides the real ones. The interval test left 8 genuine contradictions, including the
severity-3 reversal.

**The finding I'm most careful about.** The deterministic-vs-semantic ordering
reverses at severity 3 — a genuine Simpson's paradox in our own data, caused by the
severity mix differing between the groups (the deterministic group there is all F2
latency, below budget). It is real and I surfaced it; it is also n=2 and not
significant after correction, and I said that too. Reporting the reversal AND its
under-power is the whole discipline: neither hide it nor over-claim it.

**The honest headline.** After Holm correction, none of the subgroup contradictions
is individually significant at n=44. A weaker person would either bury that (and
claim a clean headline) or cherry-pick an uncorrected "significant" slice. The
defensible answer is: the spread is real, the data cannot yet certify it, and the
limitations lead the report.

**Mastery gate.**
- *Explain* — [LEARN-simpson.md](LEARN-simpson.md).
- *Build* — slicer, min-sample + Holm gate, reversal detector, audit.
- *Debug* — [`evidence/subgroup_report.json`](evidence/subgroup_report.json): the
  per-slice reversal table.
- *Measure* — gated rates + Holm; the severity-3 reversal.
- *Defend* — [`evidence/evaluation_audit.json`](evidence/evaluation_audit.json),
  [DECISIONS.md](DECISIONS.md), D17-001…D17-007.

**What I'd watch next.** A larger dataset would move the severity-3 reversal and the
low-severity misses from "directional" to significant (or refute them); the
recovery missions (18+) should be evaluated with this same subgroup gate so a
recovery policy that helps on average but hurts a slice cannot hide behind its mean.
