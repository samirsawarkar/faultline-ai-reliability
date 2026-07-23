# REFLECTION.md — five-minute mission reflection (Day 9)

**Mission.** Implement structured-output corruption (F1) and tool latency (F2)
faults with deterministic detectors, and score them.
**Fail condition.** Detector scores are not computed against injection truth. —
*Not triggered:* every score is a confusion matrix joined to the Day-8
`GroundTruthLog` by `seq`; the scorer refuses a misaligned truth log, and tests
prove the score follows the truth (scramble the labels → the confusion moves).
See [CHECKPOINT-9.md](CHECKPOINT-9.md).

**Do we need an LLM API now? No.** F1/F2 detection is schema validation and a
latency budget — deterministic, cheap, and reproducible. Building them against a
seeded injector is exactly what lets the detector's precision/recall be a *number*
rather than an anecdote. A real subject slots in behind the same `call` boundary
later (D9-004, D9-006).

**The sharpest decision.** Keeping detection and scoring apart (D9-001): the
detector may only see what the system under test sees; the scorer alone reads the
truth log. That is what makes "did it detect?" un-gameable, and it mirrors Day 8's
out-of-band labels. The join-and-guard in `score()` turns "scored against truth"
from a claim into an enforced precondition.

**The most honest result.** F1 recall is 0.667 at severity 1, not 1.0. I could
have tightened the schema to force a perfect score, but the headroom in the value
range is the point: a schema catches *malformed*, not *wrong*, so a small
in-range corruption slips through. Reporting the miss — and tracing it per call in
`trace_f1_corrupt.json` — is more valuable than a vacuous green.

**Mastery gate.**
- *Explain* — [LEARN-validation-latency.md](LEARN-validation-latency.md).
- *Build* — schema, latency, two detectors, two injectors over Day 8.
- *Debug* — [`trace_f1_corrupt.json`](evidence/trace_f1_corrupt.json): the run
  where the detector misses two small corruptions.
- *Measure* — [`detector_sweep.json`](evidence/detector_sweep.json): confusion
  matrices vs injection truth across severity and budget.
- *Defend* — [DECISIONS.md](DECISIONS.md), D9-001…D9-007.

**What I'd watch next.** F3–F6 (Missions 10–11) add schema drift, provider
failure, context corruption, and loop exhaustion — each a new family with its own
detector, scored through this same harness; then Mission 13's evaluation harness
turns these confusion matrices into a versioned dataset with intervals.
