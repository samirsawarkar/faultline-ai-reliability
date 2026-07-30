# FAULTLINE — Day 28: findings-first technical argument

Day 28 converts the five research questions into one publication package whose
claims, figures, and caveats are executable.

> **Fail condition:** a published claim has no committed result or honest
> limitation.
>
> **Status:** not triggered. The audit registers every substantive article
> paragraph, resolves every numeric token to a committed JSON result, and
> requires every finding, synthesis, and recommendation to name a limitation.

## Start with the finding

[Reliable answers, not green dashboards](ARTICLE.md) argues that recovery should
be selected on correct user-visible success under cost and latency constraints.
The five experiments establish the boundary in sequence:

1. tool depth invalidates constant-hop reliability after the shallow regime;
2. aggregate detector scores hide threshold misses and semantic escapes;
3. correlation moves the defensible retry ceiling left;
4. fallback can close availability while degrading answer quality;
5. selective guarded recovery wins in the base envelope and fails under both
   stress attacks.

The final claim is conditional. The policy is a simulator reference upper bound,
not a production deployment recommendation.

## Required evidence

| artifact | role |
|---|---|
| [ARTICLE.md](ARTICLE.md) | publication-ready findings-first article |
| [figures](evidence/figures/) | five Q1–Q5 visuals generated from result JSON |
| [FIGURE-CAPTIONS.md](FIGURE-CAPTIONS.md) | standalone population, result, and caveat for every figure |
| [claims.json](claims.json) | exact prose, JSON pointers, and limitation links |
| [claim_audit.json](evidence/claim_audit.json) | resolved values, committed Git blobs, and fail-closed checks |
| [CHECKPOINT-28.md](CHECKPOINT-28.md) | executable Day 28 gate |

## One-command publication build

From the repository root:

```bash
make day28-publication
```

This regenerates all figures, rebuilds the claim and figure manifests, and fails
if prose, results, captions, sources, or limitations drift.

Run its isolated tests with:

```bash
make test-day28
```

## Package

```text
day28/
  ARTICLE.md
  FIGURE-CAPTIONS.md
  claims.json
  figures.json
  faultline_publication/
    evidence.py
    figures.py
    audit.py
    report.py
  scripts/make_evidence.py
  tests/
  evidence/
    figures/
    claim_audit.json
    figure_manifest.json
    checkpoint_28.json
```

## Mastery gate — all five

- **Can explain** — [LEARN-findings-first.md](LEARN-findings-first.md) states the
  argument and the difference between a finding, an interpretation, and a
  deployment claim.
- **Can build** — five deterministic SVGs and one generated publication audit.
- **Can debug** — any unsupported paragraph, changed token, missing source,
  caption drift, or orphan limitation fails with an exact identifier.
- **Can measure** — Q1–Q5 retain their populations, intervals, paired tests,
  cost, latency, and attacks.
- **Can defend** — all 29 substantive paragraphs are registered against
  committed results and eight limitations.
