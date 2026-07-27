# REFLECTION.md — five-minute mission reflection (Day 18)

**Mission.** Implement bounded recovery for invalid outputs and slow tools.
**Fail condition.** Recovery is unbounded, unsafe to repeat, or lacks a budget. —
*Not triggered:* the bound is a validated policy object checked every attempt (with a
hard cap), the cost ceiling is strict and the latency ceiling bounded, and an
idempotency ledger makes retries side-effect-once. See [CHECKPOINT-18.md](CHECKPOINT-18.md).

**Do we need an LLM API now? No.** M1's "repair prompt" and M2's "tool" are
deterministic producers so the bounding, budgeting, and idempotency can be built and
proven reproducibly. A real repair model / tool drops in behind the same interface;
the envelope does not change.

**The sharpest decision.** Defining recovery by its envelope before its content
(D18-001). The retry engine is terminal by construction — it literally cannot hang or
overspend cost — so "bounded" is a property of the code, not a promise in a comment.
Everything else (what to retry) is pluggable inside that envelope.

**The idea I most wanted to get right.** Idempotency (D18-004). A bounded retry that
re-applies a side effect is still a fault, just a bounded one. The ledger demo — 3
deliveries, 1 side effect vs 3 — is the whole "safe to repeat" clause in one number,
and it is the difference between recovery and amplification.

**The honesty I kept in.** Recovery is not free. On a persistent fault it burns its
budget for zero benefit, and I reported that (cost 4, latency 34, benefit none) next
to the wins. A recovery layer that only advertises its success rate is hiding its
bill and its correctness hazard.

**Mastery gate.**
- *Explain* — [LEARN-idempotency.md](LEARN-idempotency.md).
- *Build* — policy, bounded engine, M1 repair, M2 timeout, idempotency ledger.
- *Debug* — [`evidence/recovery_traces.json`](evidence/recovery_traces.json): per-attempt spans.
- *Measure* — paired McNemar (p=0.03125) + ceiling checks.
- *Defend* — [DECISIONS.md](DECISIONS.md), D18-001…D18-007.

**What I'd watch next.** Mission 19 runs the retry-crossover experiment (Q3): where
does more retrying stop helping and start just adding cost? Then Mission 20 adds the
circuit breaker and fallback so persistent faults are cut off instead of exhausting
the budget every time.
