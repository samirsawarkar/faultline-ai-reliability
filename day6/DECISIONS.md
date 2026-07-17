# DECISIONS.md — Day 6 (replay) decision log

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-07-17 · D6-001 · Separate "replay" from "re-execution" as distinct claims
**Decision.** The report measures two columns: `replay_exact` (playback of
recorded calls) and `reexec_exact` (recompute live). They are never merged.
**Why.** The fail condition is "replay claims exceed what captured state can
reproduce." Playback is exact for anything; re-execution is exact only for a pure
function. Collapsing them would let a real-provider recording masquerade as
reproducible. Keeping them separate *is* the honesty.
**Reversal cost.** None desired — this is the mission.

### 2026-07-17 · D6-002 · Replay serves recorded outputs and computes nothing external
**Decision.** `ReplayChannel` returns stored outputs in order; it never calls a
provider.
**Why.** A replay result then cannot exceed the capture by construction. It also
makes replay offline and fast.
**Reversal cost.** None; a "verify by recompute" mode would be additive.

### 2026-07-17 · D6-003 · Divergence is loud, never silent
**Decision.** If the program requests a call the recording didn't see, or with a
different input digest, replay raises `ReplayDivergence`.
**Why.** Silently fabricating or skipping would produce a replay that doesn't
correspond to any real run — the worst failure for a forensic tool.
**Reversal cost.** None.

### 2026-07-17 · D6-004 · Capture logical versions + a schema fingerprint; guard on drift
**Decision.** Bundles store `bundle_format`, `program`, `simulator`, and a
`trace_schema_fingerprint`; `check_versions` refuses replay on mismatch.
**Why.** A bundle captured under a different schema/program can't be faithfully
replayed; better to stop than to emit a misleading "exact" result. Python/platform
are deliberately NOT in this guard — the simulator doesn't depend on them.
**Reversal cost.** Loosen to warn-instead-of-raise if a compatibility shim exists.

### 2026-07-17 · D6-005 · Real provider is a stand-in with uncaptured entropy (no LLM)
**Decision.** `FlakyProvider` injects a process-global nonce standing in for
sampling/hardware/model-drift; we do not call a real API.
**Why.** Consistent with the whole repo's deterministic thesis, and it lets the
boundary be demonstrated reliably and offline. Calling a real API would add cost,
flakiness, and a network dependency without changing the lesson.
**Reversal cost.** Swap in a real client behind the same `compute()` interface;
the boundary conclusion only gets stronger.

### 2026-07-17 · D6-006 · Commit the reproducible bundle; REPORT the non-reproducible one
**Decision.** Byte-diff `bundle_simulator.json`, `replay_simulator.json`, and
`replay_report.json`; do not commit a real-provider bundle as evidence.
**Why.** Committing a flaky bundle as if it were a stable fixture would itself be
an over-claim. The report (with differing *paths*, not volatile values) carries
the boundary deterministically. Runtime `environment.json` is informational and
excluded from the byte-diff.
**Reversal cost.** Add a clearly-labelled `bundle_flaky_example.json` (non-gated)
if an illustrative sample is wanted.
