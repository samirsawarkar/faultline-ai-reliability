# REFLECTION — five-minute mission reflection (Day 25)

**Mission.** Turn failures into replay-verified postmortems whose fixes stay
fixed.

**Fail condition.** An incident cannot flip red→green across its replay-verified
fix. — *Not triggered:* both legacy paths are stably red, both fixed paths are
stably green, and the same seed/config/test is used across each intervention.

**The most important result.** A postmortem becomes much stronger when its action
item is an executable counterfactual. “Add a guard” is weaker than showing the
same failed trace become a correct answer under the original budget.

**The semantic incident.** Strict rejection was necessary but insufficient. It
would have converted a contained failure into another unanswered request. Route
quarantine and diversity complete the fix by restoring correct service.

**The deadline incident.** Both legacy and fixed paths spend two call units and
finish accounting at latency 45. The outcome changes because the fixed policy
schedules safe overlap before the primary timeout. Resource totals alone did not
explain feasibility.

**The blameless check.** The reports name excessive judge authority,
same-provider re-entry, late feasibility checking, and missing overlap. They do
not reduce the incident to “model error” or “operator error.”

**The reproducibility check.** Each version replayed 20 times in-process and under
four fresh-process hash seeds. Fixed outputs, trace digests, and regression colors
remain stable.

**Mastery gate.**

- *Explain* — [LEARN-blameless-postmortems.md](LEARN-blameless-postmortems.md).
- *Build* — two legacy/fixed policy pairs and invariant regressions.
- *Debug* — complete trace-linked timelines and assertions.
- *Measure* — outcome, cost, latency, steps, digests, and replay state.
- *Defend* — [CHECKPOINT-25.md](CHECKPOINT-25.md), decision log, case-study claim
  boundary, and executable gate.

**What I would study next.** Run these regressions against probabilistic latency
and imperfect guard/classifier models. The fixed deterministic incidents should
become seeds in a broader distributional regression suite, not the end of
reliability testing.
