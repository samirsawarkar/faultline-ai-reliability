# CHECKPOINT-10 — F3/F4: schema-valid wrong data vs explicit provider errors

**Mission.** Separate schema-valid wrong data from explicit provider errors.

**Fail condition.** Schema-valid semantic corruption is treated as detected
without evidence. — **Not triggered.**

## What was built

Two fault families over the Day-8 injector, a correctness oracle, three layered
detectors, and a scorer that produces a false-negative analysis:

| family | kinds | detector(s) | outcome |
|---|---|---|---|
| **F3** wrong-data | `malformed_range`, `malformed_tokens`, `nonmultiple`, `drift_value`, `offbase_tokens` | schema + semantic invariant | 3 caught, **2 escape** |
| **F4** provider error | `provider_error` | explicit provider-error detector + circuit breaker | recall 1.0 |

18 tests gate it; six evidence artifacts prove it.

## The measurement (seed 20260720)

| family | precision | recall |
|---|---|---|
| F3 wrong-data | 1.0 | **0.6** |
| F4 provider error | 1.0 | 1.0 |

Per-kind detection: `malformed_range` 1.0, `malformed_tokens` 1.0, `nonmultiple`
1.0, `drift_value` **0.0**, `offbase_tokens` **0.0**, `provider_error` 1.0.

## The escape set — missed detections with evidence

`evidence/false_negatives.json` lists the two schema-valid semantic corruptions
that the mixed classifier labels `OK`, each proven wrong by the oracle:

- `drift_value` — returned `value 80` where the correct answer was `40`
  (schema-valid, a legal round ten, invariant-ok, classified `OK`).
- `offbase_tokens` — returned `tokens [6,7,8,9]` where `[4,5,6,7]` was correct
  (schema-valid consecutive run, value untouched, classified `OK`).

Both are counted as **false negatives**, never as detections — this is the fail
condition met head-on (`test_schema_valid_escapes_are_counted_as_false_negatives_not_detections`).

## Two findings

- **Escape is severity-invariant.** The escaping kinds detect at rate 0.0 for
  every severity 1..5 — unlike Day 9's F1/F2 (recall rose with severity). A big
  wrong-but-valid value is exactly as invisible as a small one.
- **The classifier boundary.** `PROVIDER_ERROR`, `MALFORMED`, and
  `INVARIANT_VIOLATION` are separable from observables; schema-valid semantic
  corruption is not — it collapses to `OK`. The boundary is documented in
  `classifier_boundaries.json`, not hidden.

## Circuit-breaker signal (F4)

Over the provider-error stream, the breaker trips **OPEN at seq 2** (2 errors in a
3-call window) and stays open — the recovery hook Mission 20 will consume.

## Mastery gate — all five

- **Explain** — `LEARN-semantic-invariants.md`: the detectability ladder and why a
  finite invariant set never closes the escape set.
- **Build** — `faultline_contracts/`: oracle, corruptions, invariant, classifier,
  breaker.
- **Debug** — `trace_f3_mixed.json`: per-call classifier verdict vs the oracle,
  fully traced.
- **Measure** — `contract_report.json` + `false_negatives.json`: detection vs
  injection truth, with the escape set quantified.
- **Defend** — `DECISIONS.md` (D10-001…D10-007); escapes are FN with evidence, the
  invariant is deliberately partial, families scored separately.
