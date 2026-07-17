# REFLECTION.md — five-minute mission reflection (Day 8)

**Mission.** Inject reproducible component faults with ground-truth labels
written at injection time.
**Fail condition.** Injected faults lack deterministic triggers or independent
truth labels. — *Not triggered:* triggers are pure functions of
`(spec, run_seed, seq, input_digest)` (byte-identical on repeat; deterministic
triggers seed-independent), and labels live only in an out-of-band
`GroundTruthLog`, provably absent from outputs and spans (0 leaks / 5 seeds).
See [CHECKPOINT-8.md](CHECKPOINT-8.md).

**Do we need an LLM API now? No.** Day 8 is an injection/labelling infrastructure
problem: the deliverable is that faults are *reproducible* and their truth is
*independent*, which is a determinism-and-hygiene property, not a model property.
The boundary wrapper speaks Day 6's `call(component, payload)` contract, so when a
real subject arrives it is injected into unchanged (D8-008).

**The sharpest decision.** Where the label lives. Writing it from the injection
*decision* into a separate log — never into the output or the span — is what
makes "did the detector catch it?" a fair question tomorrow. The `stall` mode is
the proof: its output is byte-identical to a clean call, so no function of the
sample can recover the label (D8-004, D8-007).

**The subtlest trap avoided.** Defining "no leakage" over generic mode words
(`error`, `drop`) instead of the reserved label namespace would have made the
check *fail spuriously* (a span's `status: "error"` is not a leak) — or, worse,
tempted me to weaken it until it passed. Scoping leakage to labels + fault ids,
and adding a planted-leak test to prove the scanner isn't vacuous, keeps the
guarantee both exact and honest (D8-006).

**Mastery gate.**
- *Explain* — [LEARN-chaos.md](LEARN-chaos.md): fault injection vs random chaos.
- *Build* — 10-field spec, four triggers, six modes, boundary wrapper, truth log.
- *Debug* — [`evidence/fault_trace.json`](evidence/fault_trace.json): join truth
  to trace by `span_id`.
- *Measure* — [`evidence/integrity_report.json`](evidence/integrity_report.json):
  reproducibility + leakage as counts across five seeds.
- *Defend* — [DECISIONS.md](DECISIONS.md), D8-001…D8-008.

**What I'd watch next.** A detector to grade against these labels (the first real
consumer of the truth log); correlated/burst faults (one spec that fires a run of
calls); and injecting into the real Day-3 baseline via a thin channel adapter.
