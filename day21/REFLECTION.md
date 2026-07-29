# REFLECTION.md — five-minute mission reflection (Day 21)

**Mission.** Measure whether fallback preserves availability while silently
reducing answer quality.

**Fail condition.** Availability is reported without measuring fallback quality. —
*Not triggered:* availability and fallback quality live in the same comparison
artifact, the gate requires both, and a test enforces it. See
[CHECKPOINT-21.md](CHECKPOINT-21.md).

**The most important result.** The answer is not a clean “fallback good” or
“fallback bad.” Availability rises 0.3333 and strict-quality service coverage rises
0.0833, yet the quality of delivered answers falls 0.25 and 30 bad answers reach
users. A defensible evaluation has to preserve that tension.

**The sharpest decision.** Keeping two quality denominators (D21-002). It prevents
availability from hiding harm without pretending unanswered primary requests were
high quality. The conditional metric tells the user-experience story; the service
metric tells the coverage story.

**The honesty check.** The judge misses 10/30 degraded answers. Those misses are not
smoothed into an aggregate or relabelled as correct; every seed is in
`degradation_detector.json`, and all are the exact failure slice Day 16 predicted.
The judge remains useful as an alert and indefensible as truth.

**Do we need an LLM API now? No.** This day integrates the deterministic,
validation-characterized Day-16 judge so the experimental harness and its failure
mode remain byte-reproducible. A real model must pass the same human-label and bias
validation before replacing it.

**Mastery gate.**

- *Explain* — [LEARN-availability-correctness.md](LEARN-availability-correctness.md).
- *Build* — paired scenario, metrics contract, judge adapter, detector, report.
- *Debug* — `evidence/degradation_detector.json`, including every false negative.
- *Measure* — Wilson intervals and paired McNemar tests across availability and quality.
- *Defend* — `evidence/Q4_FINDINGS.md`, [DECISIONS.md](DECISIONS.md), and the executable fail-condition gate.

**What I would watch next.** Quality-aware routing should feed recovery policy:
when the detector rejects fallback output, do we fail closed, try another tier, or
ask for human review? The answer needs a cascade budget so one provider's
degradation does not become Mission 22's downstream failure.
