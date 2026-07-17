# REFLECTION.md — five-minute mission reflection (Day 6)

**Mission.** Replay captured simulator runs exactly and document what real
providers cannot reproduce.
**Fail condition.** Replay claims exceed what captured state can reproduce. —
*Not triggered:* the report separates playback from re-execution and enumerates
what captured state cannot reproduce (`evidence/replay_report.json`
`claims_hold: true`; [LIMITATIONS.md](LIMITATIONS.md)).

**Do we need an LLM API now? No.** The "real provider" is a stand-in whose output
depends on uncaptured entropy — which is exactly what lets me demonstrate the
boundary reliably and offline. A real API would add cost and flakiness without
changing the lesson (D6-005). The simulator bundle stays byte-reproducible.

**Mastery gate.**
- *Explain* — [LEARN-reproducibility.md](LEARN-reproducibility.md): the three
  levels of "reproducible" and why temperature-0 still isn't deterministic.
- *Build* — [faultline_replay/](faultline_replay/): bundle format, capture,
  deterministic replay harness, diff, report.
- *Debug* — replay diverges loudly (`ReplayDivergence`) and refuses on version
  drift (`VersionMismatch`) instead of emitting a misleading match.
- *Measure* — the replay-difference report: simulator `reexec_exact: true`,
  flaky `false` with 8 differing fields; both `replay_exact: true`.
- *Defend* — [DECISIONS.md](DECISIONS.md) and [LIMITATIONS.md](LIMITATIONS.md):
  every claim bounded, every choice justified with its reversal cost.

**What I'd watch next.** A real-client provider behind the same `compute()` seam
to harden the boundary; statistical reproducibility (Day-3 Wilson intervals) for
evaluating a genuinely probabilistic provider, since byte-equality is the wrong
tool there.

**One honest limitation.** The non-reproducible provider is a nonce-based
stand-in, not a live model; it faithfully demonstrates *that* re-execution
diverges, but the specific failure modes of a real API (model drift, GPU
float non-associativity) are described in LEARN/LIMITATIONS, not exercised.
