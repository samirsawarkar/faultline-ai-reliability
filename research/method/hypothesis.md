# Hypotheses

| ID | Hypothesis | Prediction if true | Prediction if false | Test | Derived from (claim/gap IDs) |
|---|---|---|---|---|---|
| H4 | Measured pass^3 strictly exceeds naive (pass@1)^3 for >=4 of 6 rungs | Wilson CI of measured pass^3 strictly excludes and exceeds naive (pass@1)^3 point estimate on >=4 rungs | Wilson CI of measured contains or falls below the naive point on >=3 rungs; recomputed: NOT_TESTABLE_AS_PREREGISTERED (2 of 6 rungs valid; per-rung criterion met on R4 under both as-run and infra-excluded, not met on R2) | Wilson 95% score interval vs naive point (pass@1)^3 | C001, C002, GAP-001 |
| H5 | Deviation from naive compounding (delta = pass^3 - (pass@1)^3) is larger for cheaper rungs than frontier rungs | delta_R2 > delta_R4; concentration ratio C_3 higher on R2 than R4 | delta_R2 <= delta_R4 or rank order reversed; recomputed: NOT_TESTABLE_AS_PREREGISTERED (2 of 6 rungs valid; point estimates show delta_R2 = -0.0247 vs delta_R4 = +0.0167, but difference has 95% CI [-0.0080, 0.0922] including zero) | Pairwise difference of deviation deltas and concentration ratios | C002, GAP-002 |
