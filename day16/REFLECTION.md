# REFLECTION.md — five-minute mission reflection (Day 16)

**Mission.** Use an LLM judge only where semantic fallback quality needs it — and
prove its limits.
**Fail condition.** The judge is used without validation against trusted human
labels. — *Not triggered:* the judge is measured against a blinded human-labelled
set (agreement, κ, positional bias, slices) before any use, the real-judge adapter
refuses to run unvalidated, and the judge card forbids it from core scoring. See
[CHECKPOINT-16.md](CHECKPOINT-16.md).

**Do we need an LLM API now? Yes in principle — no in this environment.** This is
the first mission whose subject *is* a model. With no API here (and a byte-repro
requirement), I did what Days 3/6/7 did: a `RealJudgeAdapter` boundary for the real
thing, and a deterministic `SimulatedJudge` with a *known* blind spot and a *known*
positional bias, so the harness is built and verified now and a real judge is
re-validated by the same harness before use. The verification-against-a-known-answer
is deliberate: does the bias detector recover the bias I planted? (Yes — 1.0 on close
pairs, 0.0 on the fair control.)

**The sharpest decision.** Forbidding the judge from core success scoring
unconditionally (D16-006). It is tempting to let a "good enough" judge grade success;
that would quietly reinstate the eyeballing the whole project exists to replace. The
oracle owns success; the judge is a narrow assistant that must earn even that.

**The most honest number.** κ 0.50 against a human ceiling of κ 0.80. Raw agreement
(0.75) looked fine; chance-correction and the ceiling together show the judge is
*not* a human substitute on this task. Reporting the ceiling, not 1.0, is what keeps
the comparison fair — and still disqualifies the judge from standalone use.

**Mastery gate.**
- *Explain* — [LEARN-judge-reliability.md](LEARN-judge-reliability.md).
- *Build* — rubric, blinded validation set, judge adapter, agreement/bias harness.
- *Debug* — [`agreement_report.json`](evidence/agreement_report.json): the
  `borderline_tokens` failure slice and the close-pair positional bias.
- *Measure* — Cohen's κ vs the inter-rater ceiling, Wilson CI, bias vs a known control.
- *Defend* — [`JUDGE_CARD.md`](evidence/JUDGE_CARD.md), [DECISIONS.md](DECISIONS.md),
  D16-001…D16-007.

**What I'd watch next.** The recovery missions (18–22) can now use this judge — but
only as the fallback-quality gate for F3/F5, outside its failure slice, bias
mitigated, and never for core scoring. A real LLM judge should be dropped into the
adapter and re-run through this exact harness first; if its κ clears the ceiling and
its positional bias is negligible, its scope can widen — earned, not assumed.
