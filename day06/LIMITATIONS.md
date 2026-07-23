# LIMITATIONS.md — what a replay bundle can and cannot reproduce

This note is the mission's guard rail. **Fail condition: replay claims exceed
what captured state can reproduce.** So here, precisely, is the boundary.

## Two different promises (do not conflate them)

| | **Replay** (playback of recorded calls) | **Re-execution** (recompute live from inputs) |
|---|---|---|
| What it does | returns the exact bytes we recorded | runs the program again and recomputes provider outputs |
| Simulator (deterministic) | ✅ exact | ✅ exact — it's a pure function of captured state |
| Real provider (stand-in) | ✅ exact (we stored the bytes) | ❌ diverges — output depends on uncaptured entropy |

Evidence: `evidence/replay_report.json` — simulator `reexec_exact: true`, flaky
`reexec_exact: false` with 8 differing fields (`nonce`-bearing outputs → different
`sha256`), while **both** replay exactly.

## What a bundle CAN reproduce

1. **The captured simulator run, byte-for-byte** — by replay *and* by
   re-execution. The simulator is a pure function of `(seed, inputs)`, and the
   Mersenne-Twister seed is captured, so the trace is identical on any machine.
2. **Any recorded provider call, byte-for-byte** — by playback, regardless of
   whether the provider was deterministic. This is record/replay (VCR-style).
3. **A captured failure** — the same error span reappears; it is reproduced, not
   re-invented (`test_failed_run_replays_exactly`).

## What a bundle CANNOT reproduce (and we never claim it can)

1. **A real provider's output by re-execution.** Its result depends on state we
   did not (and often cannot) capture: sampling temperature and RNG, server-side
   model version, hardware/floating-point nondeterminism, concurrency. Replaying
   the *stored* bytes is playback, not reproduction of the computation.
2. **A real provider's output for an input we did not capture.** A bundle is a
   recording, not the model. Change the prompt and there is nothing to replay —
   `ReplayChannel` raises `ReplayDivergence` rather than fabricating an answer.
3. **Uncaptured runtime differences.** `evidence/environment.json` records the
   python/platform we ran on, but the bundle does **not** depend on them for the
   simulator. For a real provider or a floating-point-heavy path, those
   differences are part of the boundary and are out of scope for exact replay.

## Design choices that keep claims honest

- **Replay never computes a provider output** — it only serves recorded ones, so
  a replay result can never be more than the capture.
- **Version guard.** `check_versions` refuses to replay a bundle whose logical
  component versions or trace-schema fingerprint don't match this code, instead
  of emitting a misleading "exact" replay (`VersionMismatch`).
- **Divergence is loud.** If the program leaves the recorded path, replay raises;
  it does not silently guess.
- **We do not commit a real-provider bundle as if it were reproducible.** We
  commit the simulator bundle (which is) and *report* the real-provider boundary.
