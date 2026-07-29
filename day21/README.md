# FAULTLINE — Day 21: Q4 — silent fallback degradation

Measure whether fallback preserves availability while **silently reducing answer
quality**. Availability, oracle correctness, strict fallback quality, provenance,
and detector accuracy are reported on the same deterministic request population.

> **Fail condition:** availability is reported without measuring fallback quality.
> **Status: not triggered** — the committed comparison places availability beside
> oracle correctness, strict answer quality, strict-quality service rate, and the
> fallback-only quality slice. See [CHECKPOINT-21.md](CHECKPOINT-21.md).

## The one idea

Day 20 restored availability with a secondary provider and recorded truthful route
provenance. That is necessary, but it is not enough: `served_by=secondary` says
*where* an answer came from, not whether that answer is good.

Day 21 runs primary-only and fallback-enabled configurations on the same 120 seeds.
Every third request hits a primary outage. Fallback answers all 40 outage requests,
but only 10 meet the strict quality rubric. The availability dashboard turns green
while answer quality falls.

## Day plan delivered

| block | delivered |
|---|---|
| **08:00–10:00 · Build A** | explicit availability, oracle, strict-quality, service-quality, fallback-quality, and provenance metrics |
| **10:15–12:15 · Build B** | Day-16 validation-gated narrow judge, pointwise and advisory only |
| **13:00–15:00 · Attack + experiment** | paired 120-seed primary/fallback run plus an availability-only silent-degradation attack |
| **15:15–16:15 · Learn** | [availability versus correctness](LEARN-availability-correctness.md), including denominator traps |
| **16:30–17:30 · Evidence + market** | three JSON artifacts, [Q4 findings](evidence/Q4_FINDINGS.md), and [market note](MARKET.md) with judge caveats |

## What's here

```
faultline_fallback_quality/
  scenario.py   paired seeded primary-only/fallback-enabled requests
  metrics.py    availability, oracle, strict quality, and provenance metrics
  detector.py   validation-gated narrow judge + scored degradation detector
  report.py     comparison, paired tests, attack, fail-condition gate, Q4 answer
  findings.py   committed Markdown Q4 renderer
scripts/ make_evidence.py
tests/   test_metrics.py  test_detector.py  test_report.py  (13 tests)
evidence/
  availability_quality_comparison.json
  degradation_detector.json
  silent_degradation_attack.json
  Q4_FINDINGS.md
CHECKPOINT-21.md · LEARN-availability-correctness.md · DECISIONS.md
REFLECTION.md · MARKET.md
```

## Quickstart

```bash
python -m pytest tests/ -q       # 13 tests
python scripts/make_evidence.py  # regenerate all Q4 evidence
```

Standard library only. Builds directly on Day 1 (oracle), Day 14 (Wilson +
McNemar), Day 16 (narrow judge validation), and Day 20 (fallback provenance).

## Q4 result (N=120 paired seeds)

| configuration | availability | oracle correctness / answered | strict quality / answered | strict-quality service rate |
|---|---:|---:|---:|---:|
| primary only | 0.6667 | 1.0 | 1.0 | 0.6667 |
| fallback enabled | **1.0** | 0.9167 | **0.75** | 0.75 |

- Availability rises **+0.3333** (paired McNemar, significant).
- Strict quality among delivered answers falls **−0.25**.
- Strict-quality service rate rises **+0.0833**, because 10 fallback answers are
  useful even though 30 are bad. Reporting both denominators prevents either a
  flattering availability story or an unfair “fallback never helps” story.
- Fallback-only quality is **10/40 acceptable**; **30/40 silently degraded** while
  route provenance remains 100% complete and consistent.

## Degradation detector under attack

The attack keeps availability at 1.0 and `is_degraded=false` while corrupting
secondary answers. Availability-only and degraded-flag-only monitors raise zero
alerts.

| detector result on 40 fallback answers | count |
|---|---:|
| true positives | 20 |
| false positives | 0 |
| false negatives | 10 |
| true negatives | 10 |

Recall is **0.6667** (95% Wilson CI [0.4878, 0.8077]); precision is **1.0**
([0.8389, 1.0]). Every miss is a `borderline_tokens` example—the exact failure
slice Day 16 found.

### Judge caveat

The Day-16 judge is validation-*characterized*, not standalone-approved: κ=0.5
versus a 0.8 human ceiling, positional bias in pairwise mode, and zero agreement on
the token-order slice. Day 21 therefore uses it pointwise, only for fallback
alerts, never for core scoring. Strict human-rubric labels and the Day-1 oracle
remain the ground truth.

## Mastery map — all five

- **Explain** → [LEARN-availability-correctness.md](LEARN-availability-correctness.md)
- **Build** → `faultline_fallback_quality/` (paired scenario, metrics, detector, report)
- **Debug** → `evidence/degradation_detector.json` (every false negative by seed/slice)
- **Measure** → `availability_quality_comparison.json` (paired availability and quality)
- **Defend** → [Q4 findings](evidence/Q4_FINDINGS.md), [DECISIONS.md](DECISIONS.md),
  and explicit judge prohibitions
