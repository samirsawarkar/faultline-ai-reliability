# FAULTLINE — Day 10: F3/F4 — schema-valid wrong data vs explicit provider errors

Separate three things a contract layer must not conflate: **malformed output**
(schema catches it), **schema-valid-but-wrong data** (a validator accepts it),
and **explicit provider errors** (the call fails outright). The headline result
is honest and uncomfortable: **40% of injected wrong-data faults escape every
deterministic contract check** — and they are reported as *missed detections with
oracle evidence*, never as detections.

> **Fail condition:** schema-valid semantic corruption is treated as detected
> without evidence.
> **Status: not triggered** — the two escaping kinds (`drift_value`,
> `offbase_tokens`) are classified `OK` by the mixed classifier and counted as
> **false negatives**; each ships in `evidence/false_negatives.json` with the
> oracle's expected-vs-got diff proving it is wrong. See [CHECKPOINT-10.md](CHECKPOINT-10.md).

## The one idea

Day 9 showed a schema detector catches malformed output. Day 10 asks what it
*can't* catch. A schema answers "right shape?"; a semantic invariant answers a
little more ("value is a round ten"); only an oracle answers "right answer?".
Between the invariant and the oracle lies a set of outputs that are well-formed,
invariant-respecting, and still wrong. This mission measures that set and refuses
to pretend it's covered.

## What's here

```
faultline_contracts/
  oracle.py      the one correct answer per request (truth only; no detector uses it)
  spec.py        ContractFaultSpec + F3/F4 kinds (reuses Day-8 triggers)
  corruption.py  F3 corruptions (malformed + schema-valid-wrong) + ProviderError (F4)
  detectors.py   invariant_detect, provider_error_detect, classify (the boundary)
  breaker.py     circuit-breaker signal from provider errors
  runner.py      run_contracts: inject, label (Day-8 truth), capture observables
  score.py       detection confusion vs truth + escaped_false_negatives (evidence)
  experiment.py  mixed run, per-kind detection, severity invariance, boundaries
  cards.py       F3/F4 fault cards
scripts/
  make_evidence.py
tests/
  test_oracle_corruption.py test_detectors_breaker.py test_score_experiment.py (18)
evidence/
  fault_cards.json contract_report.json false_negatives.json
  classifier_boundaries.json trace_f3_mixed.json trace_f4_provider.json
CHECKPOINT-10.md · LEARN-semantic-invariants.md · DECISIONS.md · REFLECTION.md
```

## Quickstart

```
python -m pytest tests/ -q       # 18 tests
python scripts/make_evidence.py  # regenerate evidence (byte-reproducible)
```

Standard library only. Builds on Day 8 (injection truth), Day 9 (schema +
scoring), Day 4 (traces).

## F3 — schema drift / semantic corruption (Build A)

Five kinds, split by whether they survive the schema:

| kind | schema-valid? | caught by |
|---|---|---|
| `malformed_range` | no | schema |
| `malformed_tokens` | no | schema |
| `nonmultiple` (value not a round ten) | yes | semantic invariant |
| `drift_value` (a *different* round ten) | yes | **nothing — escapes** |
| `offbase_tokens` (shifted consecutive run) | yes | **nothing — escapes** |

## F4 — provider errors + classifier boundary (Build B)

An explicit error envelope: the call raises, there is no content. The
provider-error detector catches it with **recall 1.0**, and a **circuit-breaker
signal** trips OPEN after 2 errors in a 3-call window. The mixed `classify` layers
the three detectors and defines the boundary: `PROVIDER_ERROR`, `MALFORMED`, and
`INVARIANT_VIOLATION` are separable from observables; a schema-valid,
invariant-respecting, non-erroring output is classified `OK` even when wrong.

## Attack — which wrong values escape contract validation

`evidence/contract_report.json` (seed 20260720):

| family | precision | recall |
|---|---|---|
| **F3 wrong-data** (mixed classifier) | 1.0 | **0.6** |
| **F4 provider error** | 1.0 | 1.0 |

- **F3 recall 0.6**: of five injected wrong-data faults, three are caught (two by
  schema, one by the invariant) and **two escape** — recorded as false negatives.
- **Severity-invariant escape**: unlike Day 9's F1/F2, the escaping kinds detect
  at rate **0.0 across all severities** — a big wrong-but-valid value is exactly
  as invisible as a small one.
- **The evidence**: `false_negatives.json` lists each escape with the oracle diff,
  e.g. `drift_value` returned `value 80` where `40` was correct — schema-valid,
  invariant-ok, classified `OK`, oracle-wrong.

## Mastery map

- **Explain** → [LEARN-semantic-invariants.md](LEARN-semantic-invariants.md)
- **Build** → `faultline_contracts/` (oracle, corruptions, classifier, breaker)
- **Debug** → `evidence/trace_f3_mixed.json` (per-call verdict vs oracle, traced)
- **Measure** → `evidence/contract_report.json` + `false_negatives.json`
- **Defend** → [DECISIONS.md](DECISIONS.md), [CHECKPOINT-10.md](CHECKPOINT-10.md)
