# DECISIONS.md — FAULTLINE decision log (Day 3)

Append-only, continues Days 1–2 (D-001 … D-013).

---

### 2026-07-14 · D-014 · The baseline subject is the deterministic agent, not an LLM
**Decision.** Measure the zero point on the Day-2 deterministic agent. No API
calls.
**Why.** The mission's fail condition is "the baseline cannot be reproduced from
committed seeds and configuration." An LLM subject is not byte-reproducible even
at temperature 0 (provider/version drift), so it would fail the mission on its
own terms. A deterministic subject reproduces exactly; an LLM is the right
*subject to measure against this zero point* on a later day, not the zero point
itself.
**Reversal cost.** Adding an LLM subject is additive (a new subject adapter); it
does not touch this baseline.

### 2026-07-14 · D-015 · The entire baseline is a pure function of one frozen config
**Decision.** `BaselineConfig` (frozen) holds every constant that can move a
number — master seed, tier hop sets, step cap, cost model, latency model, Wilson
z — and is serialized into `baseline.json`.
**Why.** Reproducibility has to have a single, inspectable surface. If a constant
lived in code instead of config, the committed artifact could silently diverge
from the committed inputs. A `content_hash` over (config + aggregates) is the
one-line reproducibility check, enforced in tests and CI.
**Reversal cost.** None desired; foundational to Day 3.

### 2026-07-14 · D-016 · Per-task seeds are derived by pure arithmetic
**Decision.** `task_seed = master*1_000_003 + tier_lane*1_000_000 + i`; each tier
gets a disjoint seed lane. No global RNG, no hashing of strings.
**Why.** Deterministic, collision-free, and independent of iteration order or
`PYTHONHASHSEED`. Any task is reconstructible from `(config, tier, i)` alone.
**Reversal cost.** Changing the formula reshuffles every sampled task → a
`spec_version` bump.

### 2026-07-14 · D-017 · Tiers are hop-set distributions, and `medium` straddles the cliff
**Decision.** easy = {1,2,3}, medium = {4,5,6}, hard = {6,7,8}, with step cap 12
(solvable at ≤ 5 hops).
**Why.** If every tier were fully inside or outside the budget, success rates
would be exactly 0 or 1 and the Wilson intervals degenerate. Putting `medium`
across the cliff yields an intermediate rate and a genuinely informative interval,
which is what makes the confidence-interval work worth doing.
**Reversal cost.** Retuning tiers changes the numbers → `spec_version` bump.

### 2026-07-14 · D-018 · Cost is modeled and latency is simulated — never measured from a clock
**Decision.** Tokens come from trace lengths, cost = tokens × a committed price,
latency = a committed per-tool + per-token model. Nothing reads wall-clock time.
**Why.** Wall-clock latency is not reproducible (it depends on the machine and
load), which would break the baseline. A *modeled* latency is a stable, honest
stand-in that later days can hold fixed while they vary the thing under study.
**Reversal cost.** Swapping in real timing would require dropping the
reproducibility guarantee for latency; not contemplated for the baseline.

### 2026-07-14 · D-019 · The figure is a dependency-free, deterministic SVG
**Decision.** Render `success_vs_hops.svg` from the data as text — no plotting
library, no rasterization.
**Why.** A committed PNG is not byte-reproducible across matplotlib/OS versions,
so CI could not diff it and the artifact would rot. A hand-built SVG diffs
cleanly, renders on GitHub, and regenerates identically — a test asserts the
committed SVG equals a fresh render.
**Reversal cost.** Moving to matplotlib would add a heavy dep and forfeit the
byte-for-byte figure check; rejected.
