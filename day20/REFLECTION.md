# REFLECTION.md — five-minute mission reflection (Day 20)

**Mission.** Restore availability without hiding failures or blocking healthy traffic.
**Fail condition.** Breaker transitions or fallback provenance cannot be traced. —
*Not triggered:* every transition is logged with reason+tick, every request carries
provenance mirrored into a Day-4 trace, and a test asserts both are complete. See
[CHECKPOINT-20.md](CHECKPOINT-20.md).

**Do we need an LLM API now? No.** The breaker + fallback are control-plane logic over a
virtual-tick clock, so the whole thing is deterministic and byte-reproducible. A real
provider slots in as the primary/secondary; the state machine, provenance, and tuning are
unchanged.

**The sharpest decision.** The three-way paired study with a true no-breaker baseline
(D20-006). It stopped me from telling the flattering-but-wrong story "the breaker restored
availability." The breaker *alone* actually dips availability (it refuses calls) while
cutting 18 calls to the failing primary; the fallback is what restores availability. Two
mechanisms, two honest effects — and the breaker-only row is the one that keeps the claim
truthful.

**The honesty I'm proud of.** The degraded tier is flagged, always. It is trivially easy to
make an availability dashboard read 100% by silently serving canned answers — and that is a
worse incident than being down, because no one knows. Flagging degradation from the start is
the whole point of "without hiding failures," and it sets up Mission 21 (silent fallback
degradation) directly.

**Mastery gate.**
- *Explain* — [LEARN-breaker-degradation.md](LEARN-breaker-degradation.md).
- *Build* — CLOSED/OPEN/HALF_OPEN breaker, fallback chain, runner.
- *Debug* — [`evidence/transitions_trace.json`](evidence/transitions_trace.json): the timeline + provenance.
- *Measure* — paired availability study (naive/breaker/breaker+fb) + McNemar.
- *Defend* — [`evidence/state_diagram.svg`](evidence/state_diagram.svg), [DECISIONS.md](DECISIONS.md).

**What I'd watch next.** Mission 21 (Q4): silent fallback degradation — precisely the thing
the `is_degraded` flag is here to prevent, now measured (how often does the fallback quietly
serve worse answers, and would anyone notice?). Then Mission 22 completes the recovery matrix.
