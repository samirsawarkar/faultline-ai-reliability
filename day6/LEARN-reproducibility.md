# LEARN-reproducibility.md — reproducibility boundaries in probabilistic systems

Notes from studying where reproducibility ends, mapped to Day 6.

## Three levels of "reproducible" (they are not the same)

1. **Deterministic re-execution.** Output is a pure function of captured inputs;
   re-running recomputes the identical result. Our simulator lives here (seeded
   Mersenne Twister, no clock, no ambient entropy).
2. **Record/replay (playback).** You don't recompute; you replay recorded I/O.
   Works for *any* component, even a nondeterministic one — but it only
   reproduces the runs you recorded, and only for the inputs you saw. Our
   `ReplayChannel` is this.
3. **Statistical reproducibility.** You can't match bytes, only distributions:
   re-run many times and check the *aggregate* behavior is stable. This is the
   best you get from a genuinely probabilistic provider.

Day 6's whole point is keeping level 1 and level 2 distinct so we never sell
playback as determinism.

## Where determinism leaks in real (probabilistic) systems

- **Sampling.** Temperature > 0 draws from a distribution; even the seed may be
  server-side and unexposed.
- **"Temperature 0 ≠ deterministic."** Greedy decoding still varies in practice:
  floating-point non-associativity across GPU kernels/batch sizes, tie-breaking,
  and mixed precision make logits — and thus argmax — wobble.
- **Model version drift.** The provider silently updates weights; the same
  request returns different text next week. Uncaptured and uncapturable by us.
- **Concurrency & hardware.** Thread scheduling, non-deterministic reductions,
  different accelerators.
- **Hidden state.** Rate-limit jitter, A/B routing, caches.

None of these are in a bundle, so none can be reproduced by re-execution — only
the *recorded output* can be played back.

## The capture/replay contract that stays honest

- Capture the pure inputs (seed, prompt, tool args), the **recorded outputs** of
  every external call, the **state**, and the **versions**.
- On replay, serve recorded outputs and **recompute nothing external**. Guard on
  version drift; diverge loudly if the program goes off-path.
- Claim exactly two things, separately: *"we can replay what we recorded"* and
  *"the simulator additionally re-executes identically."* Never claim we can
  regenerate a real provider.

## Practical takeaways

- Record/replay is the right tool for regression-testing agents against captured
  provider behavior — fast, offline, exact playback — but it is a **fixture**,
  not a model.
- To evaluate a real provider you need statistical reproducibility (many runs,
  intervals — cf. Day 3 Wilson bounds), not byte equality.
- Determinism is a property you *engineer in* (seed everything, ban ambient
  entropy) — it is never free, and the boundary must be documented, not assumed.
