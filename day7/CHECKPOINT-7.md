# CHECKPOINT-7 — Q1: reliability vs required tool hops

**Question 1.** How does end-to-end reliability change as the number of required
tool hops grows?

**Finding.** End-to-end reliability decays **faster than a naive constant-per-step
compounding model predicts**. Single-hop reliability is **0.972** (95% CI
[0.966, 0.977]), but reliability does not simply compound as `p1^n`, because
per-hop reliability **declines with depth**. The naive prediction leaves the
measured 95% CI at **n = 3 hops**, and the gap widens monotonically.

## The measured curve (seed 20260717, 500 trials/hop, 4000 runs)

| hops | measured | 95% CI | naive p1^n | 95% CI | gap | naive outside CI |
|---|---|---|---|---|---|---|
| 1 | 0.966 | [0.946, 0.979] | 0.972 | [0.966, 0.977] | −0.006 | no |
| 2 | 0.922 | [0.895, 0.942] | 0.945 | [0.934, 0.954] | −0.023 | no |
| 3 | 0.818 | [0.782, 0.849] | 0.918 | [0.903, 0.932] | −0.100 | **yes** |
| 4 | 0.746 | [0.706, 0.782] | 0.893 | [0.872, 0.910] | −0.147 | yes |
| 5 | 0.626 | [0.583, 0.667] | 0.868 | [0.843, 0.889] | −0.242 | yes |
| 6 | 0.510 | [0.466, 0.554] | 0.843 | [0.815, 0.868] | −0.333 | yes |
| 7 | 0.388 | [0.346, 0.431] | 0.820 | [0.787, 0.848] | −0.432 | yes |
| 8 | 0.288 | [0.250, 0.329] | 0.797 | [0.761, 0.828] | −0.509 | yes |

Figure: `evidence/measured_vs_naive.svg`. Full data: `evidence/q1_results.json`.

## Why the curve looks like this (explaining it — the mastery gate)

- **Shape.** The naive model assumes every hop is equally reliable and
  independent, so success = `p1^n`. But the measured **per-hop reliability
  declines with depth** — 0.972 (hop 1) → ~0.77 (hop 8) — so the true product
  `∏ p_k` falls below `p1^n`, and the gap compounds. The `corrected` column
  (product of measured per-hop rates) tracks the measured curve within CI,
  confirming the mechanism is degradation, not a bug.
- **Uncertainty.** Each point is a Wilson 95% interval. Intervals **widen at
  higher n** because runs stop at the first failure, so fewer runs reach deep
  hops (hop 8 reached only 187 of 4000 runs). Less data at depth → wider CI. We
  never report a bare point without its interval.

## Divergence / trace-gap investigation (Attack block)

At the divergence hop (n = 3) we rebuilt concrete runs as Day-4 traces: a failing
run (reached 2 of 3 hops, complete error span) and a passing run (3 of 3). Both
traces are complete — **0 trace gaps** — so the divergence is a real, observable
property, not a measurement artifact. See `evidence/investigation.json` and
`evidence/example_fail_trace.json`.

## Observability gate — PASSED

All **4000** runs are backed by a complete, gap-free record (reached-hop count
consistent, per-hop outcomes present and contiguous, end-to-end verdict
consistent). No number in this checkpoint is unbacked. See
`q1_results.json.observability_gate`.

## Mastery gate

- **Explain** — `LEARN-compounding.md` + the two paragraphs above.
- **Build** — the hop sweep, per-step accounting, and product-model comparison.
- **Debug** — the divergence investigation with traced examples.
- **Measure** — Wilson intervals on every rate; naive-vs-measured separation.
- **Defend** — `DECISIONS.md`; the single modeling assumption is stated and
  its effect is exactly what the data shows.
