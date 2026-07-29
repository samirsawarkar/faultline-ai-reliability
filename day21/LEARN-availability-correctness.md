# LEARN — availability is not correctness, and correctness is not all quality

## Four questions, four denominators

A fallback incident invites one flattering number: “we answered 100% of requests.”
That number is real, but it answers only one question.

1. **Availability** = answered / all requests. Did the system return anything?
2. **Oracle correctness given answered** = grounded oracle passes / answered. Were
   delivered answers correct and sourced under the Day-1 contract?
3. **Strict quality given answered** = strict rubric passes / answered. Did the
   answer preserve value, exact context tokens, and avoid fabrication?
4. **Strict-quality service rate** = strict rubric passes / all requests. How many
   requests actually received an acceptable answer?

The conditional metric describes the quality of what users saw. The service metric
also charges the system for silence. Neither replaces the other.

Day 21 makes the distinction concrete:

| configuration | availability | strict quality / answered | strict-quality service |
|---|---:|---:|---:|
| primary only | 0.6667 | 1.0 | 0.6667 |
| fallback enabled | 1.0 | 0.75 | 0.75 |

Two apparently contradictory statements are both true:

- fallback **reduced delivered-answer quality** by 0.25;
- fallback **improved acceptable service coverage** by 0.0833.

Reporting only the first would ignore the useful fallback answers. Reporting only
the second would hide the 30 bad answers users received.

## Provenance is an index, not a certificate

Day 20's route provenance works: every request says whether it came from primary or
secondary, and the records are complete and consistent. But
`served_by=secondary` does not imply “bad,” and `is_degraded=false` does not imply
“correct.”

The route-level degraded flag describes a known delivery tier. Semantic degradation
is discovered only after examining the content. The detector uses provenance to
select the fallback slice, then applies a narrow quality judgment. This is why
provenance and quality are complementary:

```
provenance: where did this come from?
quality:    should this answer be accepted?
```

## Why a narrow judge, and why it cannot be truth

Semantic quality is where deterministic structural checks often stop helping. Day
16 built a narrow rubric and measured a simulated judge against blinded human
labels. That validation found useful behavior on clear cases and serious limits:

- Cohen's κ=0.5 versus a 0.8 human ceiling;
- pairwise positional bias;
- zero agreement on token-order drift.

Day 21 integrates the judge under those constraints. It is pointwise, fallback-only,
and advisory. The experiment's labels come from the strict human rubric, not the
judge. The Day-1 oracle separately owns core correctness.

That separation lets the detector fail honestly: it catches 20 bad fallbacks and
misses 10 token-order cases. If judge output were used as ground truth, those ten
misses would disappear from the report by definition—the measurement would be
circular.

## The silent-degradation attack

The attack keeps the properties an availability dashboard likes:

- every request receives an answer;
- every payload remains schema-valid;
- provenance is complete and consistent;
- the secondary route is not marked as the last-resort degraded tier.

It changes only semantic answer quality. An availability-only alert therefore has
no signal. A route-level flag alert also has no signal. The quality detector sees
the clear wrong and fabricated cases, while the known token-order slice escapes.

This is the practical lesson: **a fallback SLO needs a quality budget beside the
availability SLO**. A useful operating policy would alert on the fallback rate and
quality-reject rate, then sample judge-accepted fallback answers for deterministic
or human audit—especially known blind spots.

## What the experiment does not prove

- The exact rates are properties of this deterministic 120-request scenario, not a
  universal estimate for all providers or tasks.
- The judge is simulated and validation-characterized, not an API-backed model and
  not approved for standalone scoring.
- The expected-primary comparison on outage requests is counterfactual rubric
  quality, not a live primary response during downtime.
- Quality criteria are deliberately narrow (value, exact tokens, no fabrication).
  A production rubric must be revalidated for its own task and population.

The conclusion that survives those limits is structural: availability can stay
perfect while delivered-answer quality falls, so fallback quality must be measured
directly.
