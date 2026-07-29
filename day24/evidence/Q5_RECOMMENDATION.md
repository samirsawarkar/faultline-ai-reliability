# Q5 — Cascade success per unit cost and latency

**Recommendation: `P4_selective_guarded`.**

P4_selective_guarded is the only eligible policy that leads both correct successes per cost (0.6362) and per 100 latency (3.5389); its paired 95% efficiency-difference intervals versus every other eligible policy stay above zero. It returns correct visible answers at rate 0.9325 (95% CI [0.9036, 0.9532]) with mean cost 1.4656 (bootstrap CI [1.41, 1.5212]) and p95 latency 50.0 (bootstrap CI [50.0, 50.0]).

## Policy comparison (same 400 seeds)

| policy | correct visible success (95% CI) | wrong visible (95% CI) | mean cost (95% boot CI) | p95 latency (95% boot CI) | success/cost (95% boot CI) | success/100 latency (95% boot CI) | eligible |
|---|---|---|---|---|---|---|---|
| P0_no_recovery | 0.575 [0.5261, 0.6225] | 0.0 [0.0, 0.0095] | 1.0 [1.0, 1.0] | 30.0 [30.0, 30.0] | 0.575 [0.5225, 0.625] | 3.1081 [2.7121, 3.5714] | False |
| P1_bounded_retry | 0.8375 [0.7982, 0.8704] | 0.0 [0.0, 0.0095] | 1.425 [1.3775, 1.4725] | 65.0 [65.0, 65.0] | 0.5877 [0.5473, 0.6268] | 2.845 [2.5569, 3.1889] | True |
| P2_unchecked_fallback | 0.835 [0.7955, 0.8682] | 0.165 [0.1318, 0.2045] | 1.425 [1.3775, 1.4725] | 42.0 [42.0, 42.0] | 0.586 [0.5462, 0.6271] | 3.5381 [3.2252, 3.9148] | False |
| P3_full_cascade | 0.9325 [0.9036, 0.9532] | 0.0 [0.0, 0.0095] | 1.6719 [1.5869, 1.7594] | 81.0 [81.0, 98.0] | 0.5578 [0.5179, 0.6005] | 2.8576 [2.5757, 3.1751] | False |
| P4_selective_guarded | 0.9325 [0.9036, 0.9532] | 0.0 [0.0, 0.0095] | 1.4656 [1.41, 1.5212] | 50.0 [50.0, 50.0] | 0.6362 [0.6037, 0.672] | 3.5389 [3.2488, 3.8344] | True |

## Selection rule

A candidate must clear all confidence-bound thresholds for correct success, wrong-answer risk, mean cost, and p95 latency. The winner must then lead both efficiency measures, and its paired bootstrap difference intervals against every other eligible policy must stay above zero.

- eligible candidates: `['P1_bounded_retry', 'P4_selective_guarded']`
- success/cost point leader: `P4_selective_guarded`
- success/latency point leader: `P4_selective_guarded`
- uncertainty-backed dual dominance: **True**

## Paired success versus no recovery

- **P1_bounded_retry:** Δsuccess=+0.2625; discordant=105, p=3.33541e-24, significant=True.
- **P2_unchecked_fallback:** Δsuccess=+0.26; discordant=104, p=5.52529e-24, significant=True.
- **P3_full_cascade:** Δsuccess=+0.3575; discordant=143, p=1.60329e-32, significant=True.
- **P4_selective_guarded:** Δsuccess=+0.3575; discordant=143, p=1.60329e-32, significant=True.

## Winner under attack

- **worse_severity:** success=0.695 [0.6482, 0.7381], mean cost=1.7419, p95 latency=80.0, recommendation survives=False.
- **tight_budgets:** success=0.575 [0.5261, 0.6225], mean cost=1.425, p95 latency=45.0, recommendation survives=False.

The base recommendation is conditional: higher persistence/correlation breaks the success floor, while tighter per-request budgets suppress recoverable answers. Re-run selection when either operating envelope changes.

## Tradeoff statement

Selectively retrying transient faults and quality-gating one fallback avoids persistent retry waste and the full cascade's repetition path. The recommendation is not universal: both stress attacks violate at least one uncertainty-aware operating threshold.

## Model caveats

- P4 is a reference upper-bound policy: the simulator supplies the transient/persistent retryability label without classification error.
- P4's fallback guard is the strict simulator oracle, not the Day-16 narrow judge; production guard error and its cost/latency must be measured before deployment.
- Bootstrap and Wilson intervals quantify repeated-seed uncertainty inside this configured simulator, not model-form or production-shift uncertainty.

Fail-condition guard passed: **True**. The winner is never reported without cost, latency, and uncertainty.
