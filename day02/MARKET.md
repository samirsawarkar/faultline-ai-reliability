# MARKET — why the test subject is a single agent

FAULTLINE's product is *attribution*: a reproducible statement that "this
behavior change was caused by this fault." Everything about the test subject is
chosen to protect that attribution. A single, deterministic agent is the
smallest specimen that still exhibits the failure mode we care about — a system
that answers from documents and can answer while poorly grounded — with nothing
else moving.

## The argument, plainly

**1. A fault experiment is a controlled experiment.** To claim a fault caused an
effect, you change *one* thing and hold everything else fixed. The single agent
is the "everything else": deterministic (D-008), bounded (D-009), fully typed
(D-010). When Day 3 injects a fault, the fault is the only independent variable.

**2. Multi-agent systems add confounds we haven't earned yet.** More than one
agent introduces coordination, message ordering, and emergent behavior — new
sources of variation that are *themselves* nondeterministic. A behavior change in
a multi-agent run could be the injected fault, or the scheduler, or a race. That
ambiguity is the opposite of what FAULTLINE sells.

**3. You cannot debug a specimen you don't fully own.** "Fully own" (the Day-2
mission phrase) means every branch is ours and reproducible: same seed, same
task ⇒ byte-identical outcome (`tests/test_semantics.py::test_agent_is_deterministic`).
An LLM-driven or multi-agent subject would have behavior we observe but do not
control — you can't cleanly attribute a fault's effect against a baseline that
drifts on its own.

**4. Single-agent is a floor, not a ceiling.** The failure FAULTLINE studies —
plausible answer, wrong/absent grounding — already occurs in a single
retrieve-then-answer loop. If we cannot measure it honestly here, adding agents
only hides it. Establish the honest measurement on the simplest subject first;
scale the subject later, once the ruler is trusted.

## What this buys the buyer

- **Reproducible fault attribution.** Every reported effect is re-runnable to the
  byte, because the subject has no nondeterminism of its own.
- **A cheap, legible baseline.** A reviewer can read `agent.run` in a minute and
  confirm it cannot hang, cannot bypass validation, and always returns a
  structured outcome — before trusting any number built on top of it.
- **A clean upgrade path.** Faults, and later richer subjects, bolt onto a
  subject whose behavior is already pinned and judged in two independent layers
  (schema validity + semantic correctness).

**One sentence:** we test a single deterministic agent because attribution
requires a specimen with exactly one moving part, and the fault must be that
part.
