# REFLECTION.md — five-minute mission reflection (Day 7)

**Mission.** Measure how end-to-end reliability changes as required tool hops grow.
**Fail condition.** You cannot explain the measured curve and its uncertainty. —
*Not triggered:* the curve's shape is explained by measured per-hop degradation
(the `corrected` product tracks it), and its uncertainty by Wilson intervals that
widen at depth as fewer runs reach deep hops.
See [CHECKPOINT-7.md](CHECKPOINT-7.md).

**Do we need an LLM API now? No.** Q1 is a measurement/statistics question over a
seeded stochastic simulator. A real API would break reproducibility of the seed
sweep and conflate API flakiness with the compounding effect. When a real subject
arrives, this harness measures it unchanged (D7-003).

**Q1 finding.** End-to-end reliability decays faster than naive `p1^n`
compounding. Single-hop = 0.972, but the naive prediction leaves the measured
95% CI at n = 3, and by n = 8 measured is 0.288 vs naive 0.797.

**Mastery gate.**
- *Explain* — [LEARN-compounding.md](LEARN-compounding.md): why homogeneity and
  independence fail and `p^n` is only an optimistic upper bound.
- *Build* — hop sweep + per-step accounting + product-model comparison.
- *Debug* — divergence investigation with traced failing/passing runs, 0 gaps.
- *Measure* — Wilson intervals everywhere; falsification = disjoint bands at n=3.
- *Defend* — [DECISIONS.md](DECISIONS.md); the one modeling assumption is stated
  and its effect is exactly what the data shows.

**What I'd watch next.** Add correlated failures (independence-breaking) as a
second mechanism; measure whether recovery/retries bend the curve back up; and
run the same harness against a real subject once one exists.

**One honest limitation.** The per-hop degradation is a modeled stand-in for real
context/error accumulation, not observed from a live agent; it is stated openly
(D7-002) so the finding is "given this generative model, naive compounding
under-predicts and here is the measured gap and its uncertainty," not a claim
about a specific real system.
