# DECISIONS.md — Day 14 (intervals + paired statistical design) decision log

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-07-24 · D14-001 · Stdlib-only statistics (no scipy/numpy)
**Decision.** Implement `norm_ppf`, `chi2_sf(df=1)`, and binomial tails from
`math`; no third-party numeric dependency.
**Why.** Keeps the whole project's determinism/reproducibility story intact (Days
4–13 are stdlib-only) and means the statistics run identically in CI across Python
versions. The functions we need are small and well-specified.
**Reversal cost.** Low; swap in scipy behind the same API if ever desired.

### 2026-07-24 · D14-002 · Verify utilities against something INDEPENDENT
**Decision.** Verification does not re-run our code and compare to itself. Wilson
bounds are checked against the score EQUATION they solve; `norm_ppf`/`chi2_sf`
against published values and each other (`χ²₁ = Z²`); McNemar-exact against a
hand-computable binomial sum.
**Why.** The fail condition is "cannot verify." Self-comparison verifies nothing.
Checking a closed form against the equation it is supposed to satisfy, and against
external reference values, is real verification a reviewer can trust.
**Reversal cost.** None; it is the deliverable.

### 2026-07-24 · D14-003 · Wilson is the default interval; bootstrap is the general fallback + cross-check
**Decision.** Report Wilson for proportions; provide a seeded bootstrap for
arbitrary statistics and use it to cross-check Wilson.
**Why.** The normal approximation is zero-width at p=1 and can leave [0,1]; Wilson
is correct there and for small n (consistent with Days 3/7). The bootstrap covers
statistics with no closed form and, agreeing with Wilson on a proportion, doubles
as evidence the interval code is right.
**Reversal cost.** None; both are provided.

### 2026-07-24 · D14-004 · Bootstrap is seeded and deterministic
**Decision.** Resampling uses `random.Random(seed)`; same (data, seed) → same CI;
percentiles are nearest-rank (no interpolation ambiguity).
**Why.** A non-reproducible interval would break the project's determinism gate and
make CI's byte-for-byte checks impossible. Determinism is non-negotiable here.
**Reversal cost.** None.

### 2026-07-24 · D14-005 · Paired design; McNemar counts only discordant pairs
**Decision.** Compare two systems on identical seeded samples; `mcnemar_test`
operates on the two discordant counts only.
**Why.** Pairing cancels sample difficulty, so the comparison isolates the systems.
McNemar is the correct test for paired binary outcomes; concordant pairs carry no
information about a difference and must be excluded (a common analysis error is to
run an unpaired proportion test and confound difficulty with system).
**Reversal cost.** None; it is the standard method.

### 2026-07-24 · D14-006 · Exact binomial for small discordant counts, chi-square for large
**Decision.** Use the exact two-sided binomial p when discordant pairs < 25, the
continuity-corrected chi-square otherwise; report both and mark the recommended one.
**Why.** The chi-square approximation is unreliable for few discordant pairs (its
whole justification is asymptotic). The exact test is correct at any count. Marking
which to trust prevents over-claiming from a handful of pairs (e.g. 5 one-sided
pairs give p=0.0625, NOT significant).
**Reversal cost.** None; the threshold is a named constant.

### 2026-07-24 · D14-007 · Ship a plain-English interpretation guide
**Decision.** `interpret.py` + `INTERPRETATION.md` state, in words, what an interval
and a McNemar result do and do NOT license (overlap ≠ distinguishable; significant
≠ large; discordant pairs are the only evidence).
**Why.** "Can explain" is half the mastery gate. Numbers get misread constantly;
a committed guide is how the project stays honest when the reader is not a
statistician.
**Reversal cost.** None; additive.
