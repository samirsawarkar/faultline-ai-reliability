# REFLECTION.md — five-minute mission reflection (Day 22)

**Mission.** Add ceilings and repetition recovery, then compare all mechanisms by
outcome, cost, and latency.

**Fail condition.** Any mechanism lacks paired evidence or creates an unmeasured
failure. — *Not triggered:* all 36 cells are paired; every cell reports outcome,
availability, cost, and latency; all 47 induced harms reconcile. See
[CHECKPOINT-22.md](CHECKPOINT-22.md).

**What changed my view.** The aggregate success column is useful and dangerous.
M5 looks worse there because containment is not correctness, even though it halves
F6 tail latency and prevents runaway cost. M4 looks strong on availability while
still delivering six bad answers. Recovery needs a vector, not a winner.

**The sharpest decision.** Adding clean controls to every fault cell (D22-003).
Without them, M3, M5, and M6 would look harmless: the suite would never ask them to
process a healthy request after an outage, a legitimate long plan, or valid
pagination. The controls turned caveats into paired regressions.

**The honesty check.** F3 and F5 have no winner. The matrix refuses to nominate the
cheapest tied mechanism because none improves correct success. That empty answer is
more useful than a forced recommendation: semantic rejection/re-grounding remains
an unfilled recovery slot.

**The composition lesson.** M5 should wrap the system, not replace a fault-specific
recovery. Inside it, diagnose before selecting M1/M2/M3+M4/M6, then validate the
result. Enabling everything is not defense in depth when each layer can create its
own failure.

**Mastery gate.**

- *Explain* — [LEARN-recovery-composition.md](LEARN-recovery-composition.md).
- *Build* — M5 ceilings, M6 repetition recovery, shared M1–M6 experiment.
- *Debug* — `evidence/recovery_attacks.json`, all harms by seed/type.
- *Measure* — 36 paired cells with outcome, cost, latency, and uncertainty.
- *Defend* — `evidence/SIX_MECHANISM_MATRIX.md`, decisions, and checkpoint gate.

**What I would watch next.** The composition order is now explicit, but the
mechanisms are still scored mostly in isolation. A future cascade experiment
should run the composed policy end-to-end and test whether one recovery's output
triggers the next mechanism or consumes its budget.
