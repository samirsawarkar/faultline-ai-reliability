# CHECKPOINT-21 — Q4: silent fallback degradation

**Mission.** Measure whether fallback preserves availability while silently
reducing answer quality.

**Required evidence.** Availability/quality comparison, degradation detector, and
Q4 findings — all committed under `evidence/`.

**Fail condition.** Availability is reported without measuring fallback quality. —
**Not triggered.**

## What was built

- **Paired experiment** — primary-only and fallback-enabled configurations run on
  the same 120 deterministic request seeds and primary outage.
- **Metric contract** — availability, Day-1 oracle correctness, strict human-rubric
  quality, strict-quality service rate, fallback-only acceptance, silent
  degradation, and provenance completeness/consistency, all with denominators and
  Wilson intervals.
- **Degradation detector** — Day-20 provenance selects fallback outputs; the Day-16
  narrow judge supplies pointwise alerts behind a validation gate.
- **Attack** — schema-valid fallback corruptions keep every request answered and
  leave the route-level `is_degraded` flag false.
- **Inference** — McNemar tests on aligned per-seed availability, strict service
  success, and expected-primary versus fallback quality.

13 tests gate it; four evidence artifacts prove it.

## Availability and quality (same 120 seeds)

| configuration | availability | oracle correct / answered | strict quality / answered | strict-quality service |
|---|---:|---:|---:|---:|
| primary only | 0.6667 | 1.0 | 1.0 | 0.6667 |
| fallback enabled | **1.0** | 0.9167 | **0.75** | 0.75 |

- Availability: **+0.3333**; paired difference significant.
- Strict quality among delivered answers: **−0.25**.
- Strict-quality service rate: **+0.0833**; the fallback adds 10 good answers but
  also delivers 30 bad ones.
- Fallback slice: **10/40** strictly acceptable, **30/40** silently degraded.
- Provenance: **120/120 complete and consistent**. Provenance identifies the route;
  it does not certify semantic quality.

## Detector and attack

The availability-only monitor sees 1.0 and raises **0 alerts**. The
`is_degraded`-only monitor also raises **0**, because the secondary tier is
truthfully a fallback route but is not pre-labelled semantically degraded.

The quality detector scores:

```
TP=20  FP=0  FN=10  TN=10
recall=0.6667 [0.4878, 0.8077]
precision=1.0 [0.8389, 1.0]
```

All ten false negatives are committed by seed in
`evidence/degradation_detector.json`; every one is `borderline_tokens`, reproducing
the Day-16 judge's known failure slice.

## Q4 finding

**Yes, fallback can preserve availability while silently reducing answer
quality.** In this experiment it restores availability to 1.0, but lowers strict
quality among answered requests to 0.75. It still improves strict-quality service
coverage from 0.6667 to 0.75, so the defensible conclusion is not “disable
fallback.” It is: operate fallback with a quality budget, provenance, semantic
alerts, and audits for the judge's blind spots.

## Judge caveats

- κ=0.5 versus a 0.8 human inter-rater ceiling.
- Not validated for standalone use; forbidden from core success scoring.
- Used pointwise only; pairwise mode has positional bias.
- Known `borderline_tokens` blind spot remains and is measured as 10 false negatives.
- Day-1 oracle and strict human-rubric labels remain ground truth.

## The fail condition, refused

`availability_quality_comparison.json` contains availability and fallback quality
in one artifact. `fail_condition_guard` requires both, requires the judge to remain
outside core scoring, and requires every detector false negative to be surfaced.
`passed=true`; a test enforces all four conditions.

## Mastery gate — all five

- **Explain** — `LEARN-availability-correctness.md`: availability, correctness,
  strict quality, and why all denominators matter.
- **Build** — `faultline_fallback_quality/`: paired scenario, metrics, detector,
  report, findings renderer.
- **Debug** — `degradation_detector.json`: every miss carries seed, slice, judge
  verdict, and strict quality score.
- **Measure** — `availability_quality_comparison.json`: paired rates, Wilson
  intervals, and McNemar tests.
- **Defend** — `Q4_FINDINGS.md` + `DECISIONS.md`: conclusion, fail-condition gate,
  and explicit judge caveats.
