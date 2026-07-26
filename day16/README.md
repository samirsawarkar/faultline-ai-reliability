# FAULTLINE — Day 16: validate a narrow LLM judge (and prove its limits)

Introduce an LLM judge *only* where deterministic detection provably cannot reach —
the semantic escapes Q2 (Day 15) isolated — and **validate it against trusted human
labels before it is used for anything**. The deliverable is the validation harness
and a judge card that forbids the judge from core success scoring.

> **Fail condition:** the judge is used without validation against trusted human
> labels.
> **Status: not triggered** — the judge is measured against a blinded human-labelled
> set (agreement, Cohen's κ, positional bias, failure slices) *before* any use, the
> real-judge adapter refuses to run unvalidated, and the judge card forbids it from
> core scoring. See [CHECKPOINT-16.md](CHECKPOINT-16.md).

## The one idea

The oracle (Day 1) owns "did the system succeed" and always will. But the F3/F5
semantic escapes need a *semantic* judgement of fallback quality that no
deterministic check can give. An LLM judge can help there — but only if you first
prove how far it agrees with humans and where it breaks. An unvalidated judge is
worse than no judge: it launders a guess into a number.

## A note on reproducibility

This environment has no LLM/API access, and FAULTLINE is deterministic end to end.
So, exactly as Days 3/6/7 used seeded stand-ins with the real subject plugging in
later, Day 16 ships a `RealJudgeAdapter` (the API boundary; refuses to run without a
validated client) and a `SimulatedJudge` with a **known** blind spot and a
**configurable, known** positional bias. That lets the validation harness be built,
verified, and run byte-reproducibly — and lets the bias detector be checked against
a judge whose bias we already know (the Day-14 verification stance). A real judge
drops into the adapter and is re-validated by the same harness before use.

## What's here

```
faultline_judge/
  rubric.py         the narrow fallback-quality rubric (3 explicit criteria)
  validation_set.py 24 blinded human-labelled items + a 2nd human rater
  judge.py          Judge adapter: SimulatedJudge (known flaws) + RealJudgeAdapter stub
  agreement.py      raw agreement, Cohen's kappa, confusion, positional bias, slices
  report.py         the validation verdict (conservative)
  card.py           the judge card with explicit prohibitions
scripts/ make_evidence.py
tests/   test_rubric_agreement.py test_report_forbid.py  (12 tests)
evidence/
  judge_rubric.md validation_set.json agreement_report.json JUDGE_CARD.md
CHECKPOINT-16.md · LEARN-judge-reliability.md · DECISIONS.md · REFLECTION.md
```

## Quickstart

```
python -m pytest tests/ -q       # 12 tests
python scripts/make_evidence.py  # regenerate rubric, validation set, agreement report, judge card
```

Standard library only (Day 14 for Wilson intervals). No network, no API key.

## Validation result (24 blinded human labels)

- **judge vs human:** raw agreement 0.75 (95% CI [0.55, 0.88]), **Cohen's κ 0.50
  (moderate)** — the confusion shows the judge is **lenient** (6 false accepts, 0
  false rejects).
- **human-vs-human ceiling:** κ 0.80 (substantial) — the judge sits *below* the
  human reliability ceiling, so it is not a drop-in for a human.
- **failure slice:** `borderline_tokens` (agreement 0.0) — the judge tolerates
  token-order drift that humans reject.
- **positional bias:** close pairwise calls are **100% order-dependent** (the judge
  picks whatever is presented first when it can't tell candidates apart); the fair
  control shows 0.0, confirming the detector recovers a *known* bias.

## Verdict + prohibition (the fail condition, refused)

`validated_for_standalone_use = False`; `forbidden_from_core_success_scoring =
True`. `JUDGE_CARD.md` states the enforced prohibitions: the judge **must not**
contribute to core success scoring (the oracle owns that), **must not** be trusted
inside its failure slice, and any real judge **must pass this harness** before use.
`RealJudgeAdapter.accept` raises until a client is configured *and* validated.

## Mastery map

- **Explain** → [LEARN-judge-reliability.md](LEARN-judge-reliability.md)
- **Build** → `faultline_judge/` (rubric, validation set, judge adapter, harness)
- **Debug** → `evidence/agreement_report.json` (per-slice + positional-bias breakdown)
- **Measure** → agreement + Cohen's κ vs the human ceiling, with a Wilson CI
- **Defend** → `evidence/JUDGE_CARD.md`, [DECISIONS.md](DECISIONS.md), [CHECKPOINT-16.md](CHECKPOINT-16.md)
