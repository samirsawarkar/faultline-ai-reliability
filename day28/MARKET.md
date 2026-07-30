# MARKET — coordinated publication package

## Publication thesis

> Availability is necessary but insufficient: recovery earns trust only when it
> improves correct user-visible success inside explicit cost and latency limits.

This is the coordinated sentence for the article, repository release notes,
technical social post, and architecture-review briefing. Each surface should link
to the article rather than restating unsupported numbers.

## Assets

| surface | asset | purpose |
|---|---|---|
| long form | [ARTICLE.md](ARTICLE.md) | complete technical argument |
| repository | [README.md](README.md) | reproducibility and evidence map |
| visual thread | [five figures](evidence/figures/) | one Q1–Q5 finding per panel |
| reviewer packet | [FIGURE-CAPTIONS.md](FIGURE-CAPTIONS.md) | portable captions |
| verification | [claim audit](evidence/claim_audit.json) | claim-to-result proof |
| release gate | [Checkpoint 28](CHECKPOINT-28.md) | publication readiness |

## Audience sequence

1. **Reliability engineers:** lead with retry correlation and fallback quality.
2. **AI platform teams:** lead with the outcome contract and semantic-judge
   caveat.
3. **Product and finance:** lead with correct success per cost and latency, then
   the attacks that withdraw the winner.
4. **Researchers:** lead with shared seeds, uncertainty-aware selection, and the
   committed claim ledger.

## Coordinated release checklist

- Freeze the article and all five figures from one commit.
- Publish the article URL and repository revision together.
- Use the standalone caption verbatim when a figure leaves the article.
- State “simulator reference upper bound” wherever P4 is named.
- Link the machine claim audit in technical and reviewer-facing publication.
- Do not call the detector standalone validated.
- Do not claim Q1 divergence at hops 1 or 2.
- Do not claim either stress attack preserved the Q5 recommendation.
- Re-run `make day28-publication` and `make test-day28` immediately before
  publication.

## Short coordinated copy

We tested five places where AI recovery claims can become misleading: tool depth,
fault detection, retries, fallback, and cascade policy. The result is conditional
but actionable: selective, bounded, quality-gated recovery improves correct
user-visible outcomes in the measured base envelope; availability alone hides
degradation, and both stress attacks withdraw the winning policy. Every
substantive paragraph and figure is linked to a committed result and an explicit
limitation.
