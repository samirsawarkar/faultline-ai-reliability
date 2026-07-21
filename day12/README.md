# FAULTLINE — Day 12: fault catalog + gallery

Consolidate F1–F6 (Days 8–11) into one defensible, reproducible experimental
specification: **six complete fault cards**, a **gallery** linking fault → trace →
detector → metric, **labelled traces**, a reproducibility + ground-truth integrity
**audit**, and a **failure taxonomy by producing component**.

> **Fail condition:** any fault card lacks trigger, trace, detector, recovery, or
> metric.
> **Status: not triggered** — `FaultCard.validate()` rejects a card missing any of
> the five required fields (and requires the normalized 10-field spec); the audit
> confirms all six cards are complete. See [CHECKPOINT-12.md](CHECKPOINT-12.md).

## The one idea

The last four days each produced a fault family and measured it. This day makes
the whole thing *citable*: every fault is normalized to the same 10-field spec and
written as a card carrying its trigger, a labelled trace, its detector, its
recovery plan, and its measured metric — with each metric pulled live from the day
that measured it, so the catalog can never drift from the evidence.

## What's here

```
faultline_catalog/
  cards.py      the six FaultCards (normalized 10-field spec + 5 required fields)
  catalog.py    build_catalog: fill live metrics (Days 9-11) + trace refs, validate
  traces.py     one canonical labelled trace per fault (via the owning day + Day 4)
  gallery.py    fault -> trace -> detector -> metric as JSON / Markdown / HTML
  taxonomy.py   failure taxonomy by producing component
  audit.py      reproducibility + ground-truth integrity + completeness audit
scripts/ make_evidence.py
tests/   test_catalog.py test_audit.py  (12 tests)
evidence/
  catalog.json GALLERY.md catalog.html audit_report.json taxonomy.json
  traces/F1.json … F6.json
CHECKPOINT-12.md · LEARN-taxonomy.md · DECISIONS.md · REFLECTION.md
```

## Quickstart

```
python -m pytest tests/ -q       # 12 tests
python scripts/make_evidence.py  # regenerate the catalog, gallery, audit (byte-reproducible)
```

Standard library only. Reads Days 8–11 (fault families + metrics) and Day 4 (traces).

## The six cards (the gallery)

Every card has all five required fields; here is the fault → detector → metric spine:

| Fault | Producing component | Detector (nature) | Recall | Recovery |
|---|---|---|---|---|
| **F1** structured-output corruption | tool output | schema (deterministic) | 1.0 (0.667 @sev1) | repair + retry |
| **F2** latency / timeout | provider transport | duration vs budget (deterministic) | 1.0 | timeout + retry |
| **F3** schema drift / wrong data | tool output | schema + invariant (mixed) | 0.6 | semantic validation |
| **F4** provider error | provider transport | explicit flag (deterministic) | 1.0 | circuit breaker + fallback |
| **F5** context corruption | agent context | consistency invariant (semantic) | 0.5 | context re-grounding |
| **F6** loop exhaustion | agent control loop | repetition + budget (deterministic) | 1.0 | step-budget cap |

Full detail in `evidence/GALLERY.md` and the HTML gallery `evidence/catalog.html`.

## Attack — the audit

`evidence/audit_report.json` (all pass):

- **reproducible** — every fault's canonical trace regenerates byte-identically,
  and the whole catalog rebuilds identically (checked across hash seeds).
- **no_label_leakage** — a fault's ground-truth labels/ids never appear in its
  observable trace, across all six (Day-8 out-of-band discipline holds catalog-wide).
- **cards_complete** — all six cards carry trigger, trace, detector, recovery, metric.
- **detectors_scored_vs_truth** — every metric is a real number measured against
  the injection log, with the day that measured it.

## Failure taxonomy by producing component (Learn)

`evidence/taxonomy.json`: faults grouped by the component that produces them.

- **Provider boundary** — F1–F4: content faults (F1 malformed, F3 semantic wrong)
  and transport faults (F2 timing, F4 availability).
- **Agent internals** — F5 (context/state, semantic) and F6 (control loop,
  deterministic).

The headline: transport and control faults are deterministic to detect;
value faults inside the data plane and the agent's context are where semantics bite.

## Mastery map

- **Explain** → [LEARN-taxonomy.md](LEARN-taxonomy.md)
- **Build** → `faultline_catalog/` (cards, catalog, gallery)
- **Debug** → `evidence/traces/*.json` (one labelled, gapless trace per fault)
- **Measure** → `evidence/catalog.json` (live metrics) + `audit_report.json`
- **Defend** → [DECISIONS.md](DECISIONS.md), [CHECKPOINT-12.md](CHECKPOINT-12.md)
