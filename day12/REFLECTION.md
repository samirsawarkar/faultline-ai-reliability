# REFLECTION.md — five-minute mission reflection (Day 12)

**Mission.** Consolidate every fault into a defensible, reproducible experimental
specification.
**Fail condition.** Any fault card lacks trigger, trace, detector, recovery, or
metric. — *Not triggered:* `FaultCard.validate()` rejects any card missing one of
the five fields (or the normalized 10-field spec), `build_catalog` validates every
card, and the audit confirms all six are complete. See [CHECKPOINT-12.md](CHECKPOINT-12.md).

**Do we need an LLM API now? No.** This is a consolidation mission: it indexes
work already done deterministically. The only forward-looking field is `recovery`,
and even there each card is grounded in a signal already emitted today (repair,
timeout, circuit-breaker, loop-detect) rather than promising an unbuilt mechanism.

**The sharpest decision.** Pulling metrics live from the owning day (D12-003) and
regenerating traces from the owning runner (D12-004), instead of copying numbers
and files. A catalog of copied facts is a liability — it drifts silently. A catalog
that re-derives from source cannot lie about the code as it stands.

**The satisfying moment.** The producer-first taxonomy (Learn) explained Day 11's
deterministic-vs-semantic split without restating it: value-correctness faults come
from exactly the two components that hold values (the data plane and the agent's
context), and only a correctness model can judge a value. The split isn't a
coincidence of the detectors we chose — it's a property of where faults are born.

**Mastery gate.**
- *Explain* — [LEARN-taxonomy.md](LEARN-taxonomy.md).
- *Build* — cards, catalog, gallery (JSON/MD/HTML), taxonomy, audit.
- *Debug* — [`evidence/traces/`](evidence/traces): one labelled, gapless trace per fault.
- *Measure* — [`evidence/catalog.json`](evidence/catalog.json) +
  [`audit_report.json`](evidence/audit_report.json).
- *Defend* — [DECISIONS.md](DECISIONS.md), D12-001…D12-007.

**What I'd watch next.** Mission 13 builds the evaluation harness + versioned
dataset on top of this catalog; Mission 14 adds intervals and paired design; and
Mission 15 (Q2) measures detection accuracy per family with Wilson CIs — the
catalog is the input those missions consume.
