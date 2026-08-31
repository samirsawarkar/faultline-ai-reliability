# FAULTLINE — one-minute engineering brief

## The decision this work enables

FAULTLINE is a reproducible reliability workbench for document-grounded AI
systems. It answers a question production dashboards often miss:

> Did recovery improve the correct user-visible outcome, or did it only make the
> service look available?

The repository treats correctness, availability, wrong answers, cost, latency,
and provenance as separate measurements. Recovery policies become eligible only
after they satisfy explicit outcome and budget constraints; efficiency is
compared afterward.

## Five findings worth inspecting

| Engineering question | Committed finding | Why it matters |
|---|---|---|
| Does tool depth behave like repeated identical calls? | The naive reliability estimate first separated from the measured interval at **3 hops**. [Evidence](day07/evidence/q1_results.json) | End-to-end reliability cannot be inferred from a single-hop success rate when later steps are harder. |
| Can an aggregate detector score hide operational risk? | The detector had **10 false negatives**; 4 were semantic escapes. The proposed judge reached only **0.5 kappa** and was excluded from core success. [Detector](day15/evidence/q2_results.json) · [judge](day16/evidence/agreement_report.json) | A detector must be validated on its miss slices before it receives decision authority. |
| Is a retry cap stable across fault structure? | The last cap inside the configured ceilings moved from **K=3** under independent faults to **K=2** under correlated faults. [Evidence](day19/evidence/crossover.json) | During shared failure, retry can amplify the impaired dependency instead of repairing the request. |
| Does fallback preserve service quality? | Availability rose from **0.6667 to 1.0**, while strict quality among answered requests fell from **1.0 to 0.75**. [Evidence](day21/evidence/availability_quality_comparison.json) | “We returned an answer” is not a sufficient reliability outcome. |
| Which recovery policy wins after cost and latency are included? | The base winner reached **0.9325** correct success at **1.4656** mean cost and **50.0** p95 latency, then failed its thresholds under both stress attacks. [Comparison](day24/evidence/policy_comparison.json) · [attack](day24/evidence/winner_attack.json) | The recommendation is useful only inside the measured operating envelope. |

The publication audit binds each registered article claim to its source,
location, rendering, limitation, and Git revision:
[claim_audit.json](day28/evidence/claim_audit.json).

## What the engineering work demonstrates

- **Outcome ownership:** defines user-visible success before choosing a recovery
  mechanism.
- **Experimental judgment:** uses shared seeds, paired comparisons, uncertainty
  intervals, and stress attacks instead of unpaired dashboard averages.
- **Systems thinking:** models propagation across tool depth, detection, retry,
  circuit breaking, fallback, budgets, and quality gates.
- **Operational discipline:** preserves complete traces, causal labels,
  deterministic replay, red→green regressions, and fail-closed checkpoints.
- **Research integrity:** excludes an under-validated semantic judge from the
  success oracle and publishes the limits that reverse each recommendation.
- **Delivery discipline:** provides exact dependency and action pins, a
  digest-pinned clean container, one-command reproduction, and continuously
  checked evidence.

## Ten-minute evaluation path

1. Run `make reproduce-fast` or inspect the current
   [CI workflow](https://github.com/samirsawarkar/faultline-ai-reliability/actions/workflows/ci.yml).
2. Follow one incident through the
   [case study](day29/CASE-STUDY.md),
   [before/after traces](day25/evidence/red_green_replay.json), and regression
   tests.
3. Challenge the policy choice using the
   [Q5 recommendation](day24/evidence/Q5_RECOMMENDATION.md) and its stress
   attacks.
4. Ask any question in the [defense guide](day30/DEFENSE.md), especially what
   evidence would reverse the decision.

## Honest scope

This is a seeded, synthetic research workbench, not a production deployment or
a claim of universal model reliability. Its confidence intervals describe the
configured experimental populations. Provider independence, real traffic
distributions, model drift, and human rubric validity still require production
measurement.

That boundary is intentional: the strongest signal in FAULTLINE is not that it
never fails. It is that a recommendation must remain traceable, budgeted,
replayable, and withdrawable when evidence changes.
