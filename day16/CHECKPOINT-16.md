# CHECKPOINT-16 — validate a narrow LLM judge

**Mission.** Use an LLM judge only where semantic fallback quality needs it — and
prove its limits.

**Fail condition.** The judge is used without validation against trusted human
labels. — **Not triggered.**

## What was built

A narrow, validated-before-use LLM judge for the semantic escapes Q2 isolated:

- **A narrow rubric** — one question (is this fallback acceptable?), three explicit
  criteria, scoped only to F3 `drift_value` / F5 `context_drift`.
- **A blinded human-labelled validation set** — 24 items across 4 slices, plus a
  second human rater for the inter-rater ceiling.
- **A judge adapter** — `SimulatedJudge` (deterministic, with a known blind spot and
  configurable known positional bias) + `RealJudgeAdapter` (refuses to run
  unvalidated).
- **An agreement + bias harness** — raw agreement, Cohen's κ, confusion, positional
  bias (both-orders), per-slice, and a conservative verdict.

12 tests gate it; four evidence artifacts prove it.

## Validation result (24 trusted human labels)

| metric | value |
|---|---|
| judge vs human — raw agreement | 0.75 (95% CI [0.55, 0.88]) |
| judge vs human — **Cohen's κ** | **0.50 (moderate)** |
| human-vs-human ceiling — κ | 0.80 (substantial) |
| judge confusion (accept = positive) | tp 6, **fp 6**, fn 0, tn 12 → **lenient** |
| failure slice | `borderline_tokens` (agreement 0.0) |
| positional bias (close pairs) | **1.0 order-dependent** (fair control 0.0) |

The judge agrees with humans on clear cases, sits below the human reliability
ceiling, over-accepts, has a zero-agreement failure slice (token-order drift), and is
fully order-dependent on close pairwise calls — the fair control confirms the bias
detector reports 0 when there is genuinely no bias.

## Verdict + prohibition (the fail condition, refused)

- `validated_for_standalone_use = False` (fails the conjunctive bar: κ < 0.80, bias
  > 0.05, a dead slice exists).
- `forbidden_from_core_success_scoring = True` — **unconditionally**. Core success is
  the Day-1 oracle's job; the judge is a fallback-quality assistant only.
- `RealJudgeAdapter.accept` raises until a real client is configured *and* re-validated
  by this harness.

## Mastery gate — all five

- **Explain** — `LEARN-judge-reliability.md`: raw vs κ, the human ceiling, LLM-judge
  biases, and why the judge is confined.
- **Build** — `faultline_judge/`: rubric, validation set, adapter, harness, card.
- **Debug** — `agreement_report.json`: per-slice + positional-bias breakdown pinpoint
  where the judge fails.
- **Measure** — Cohen's κ vs the inter-rater ceiling, with a Wilson CI; positional
  bias recovered against a known control.
- **Defend** — `JUDGE_CARD.md` + `DECISIONS.md` (D16-001…D16-007): validate first,
  forbid from core scoring, narrowest possible job.
