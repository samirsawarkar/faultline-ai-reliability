# LEARN — context integrity and termination correctness

Day 11 closes the fault spectrum with the two families that sit at opposite ends
of the detectability axis: **context corruption** (the quietest fault in the
catalog) and **loop exhaustion** (the loudest). Understanding why they sit where
they do is the whole lesson, and it is the foundation for Q2.

## Two kinds of "wrong"

A fault is detectable *deterministically* when noticing it needs only structure,
counts, equality, or an explicit flag — no idea of what the right answer is. A
fault is detectable only *semantically* when noticing it needs a model of
correctness: a value invariant, an oracle, or a validated judge. The six FAULTLINE
faults split cleanly along this line:

- **Deterministic:** F2 latency (a number vs a budget), F4 provider error (an
  explicit flag), F6 loop exhaustion (a step count and a repeated-step check), and
  the *malformed* subsets of F1/F3 (a schema).
- **Semantic:** F3 schema-valid drift (`drift_value`, `offbase_tokens`) and F5
  context corruption (`context_drift`) — well-formed, plausible, and wrong.

The line is not about difficulty of *engineering*; the deterministic detectors are
often trivial. It is about whether detection needs a *reference for correctness*.
That is why no amount of cleverness makes a schema catch `drift_value`: the
corrupted output is structurally indistinguishable from a correct one.

## Context integrity: consistency is not correctness

F5 shows the subtlety inside the semantic side. A cheap **consistency invariant**
(`final == sum(context)`) is not deterministic in our sense — it encodes a domain
meaning — but it also is not the oracle. It catches an *incoherent* corruption
(`context_inconsistent`, where the final no longer matches the context) and misses
a *coherent* one (`context_drift`, where the final was recomputed to match). The
lesson mirrors Day 10's invariant ladder: consistency checks raise the floor and
should always be used, but a self-consistent lie passes them. Context corruption is
especially dangerous because it **propagates** — a wrong value entered early flows
through every later step, and each step's local view is perfectly consistent. Only
a check against ground truth (an oracle, or agreement across independent sources)
catches it.

## Termination correctness: bounded by construction, verified by counting

F6 is the opposite. Termination is a **structural** property: FAULTLINE's agent
loop is bounded by a step cap (Day 2 made termination structural, not a hoped-for
timeout; Day 7 turned the hop cap into a measured fault). So "did it terminate
correctly?" reduces to two counts: *did it exceed the budget without completing?*
and *did it repeat a step instead of progressing?* Both are decidable with no model
of the answer, which is why F6 is caught at recall 1.0 with zero escape. The
engineering rule: **make termination structural, then a counter is a complete
detector.** Repetition detection matters because a loop can stay under budget while
making no progress — livelock, not just deadlock — so counting steps is necessary
but not sufficient; you also watch for repeated state.

## Why this split is the setup for Q2

If detection accuracy were uniform, you could report one number and be done. It is
not: the spectrum splits, and the split is *structural*, not a tuning artifact. The
Q2 split hypothesis states it precisely — deterministic faults approach recall 1.0
with cheap detectors and no residual; semantic faults have an irreducible escape
set under any deterministic detector and need semantic evaluation. Committing this
as a falsifiable hypothesis (with a named refuter that cannot exist by
construction) is what lets Mission 15 measure detection accuracy honestly, per
family and with intervals, instead of averaging a real bimodal distribution into a
misleading single figure.

## References worth reading next

- Termination and bounded execution: total vs partial correctness (any formal
  methods text); livelock vs deadlock (Tanenbaum, *Modern Operating Systems*).
- Context / data-flow integrity and error propagation: taint tracking, and the
  "garbage in, garbage out" propagation problem in pipelines.
- Consistency vs correctness: the CAP/consistency literature for the systems
  sense, and the oracle problem (Barr et al., 2015) for the testing sense.
