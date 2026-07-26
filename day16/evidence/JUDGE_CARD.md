# JUDGE CARD — narrow fallback-quality judge

## Scope (narrow, by design)
narrow fallback-quality for F3 drift_value / F5 context_drift only. The judge answers ONE question — "is this fallback
candidate acceptable under the Day-16 rubric?" — for the semantic escapes that no
deterministic detector can catch (Q2, Day 15). It does nothing else.

## Validation against trusted human labels (n = 24)
- judge vs human: raw agreement 0.75 (95% CI [0.551, 0.88]),
  Cohen's kappa **0.5 (moderate)**
- human-vs-human ceiling: kappa 0.8 (substantial) — the judge
  is measured against this, not against a perfect 1.0
- confusion (accept = positive): {'tp': 6, 'fp': 6, 'fn': 0, 'tn': 12}
  (the judge is LENIENT — it over-accepts)

## Known limits
- **Failure slice(s): ['borderline_tokens']** — the judge tolerates
  token-order drift that humans reject; do not trust it alone there.
- **Positional bias: 0.5** of paired comparisons are
  order-dependent (close pairs: 1.0).
  Use pointwise scoring, or average both presentation orders.

## PROHIBITIONS (enforced)
1. **The judge MUST NOT contribute to core success scoring.** Core success is
   decided solely by the Day-1 required-source oracle. The judge is a fallback-
   quality assistant, never the arbiter of whether the system succeeded.
2. **Do not use the judge inside its failure slice** (token-order) without a human
   check.
3. **Any real LLM judge must pass this exact validation harness** (agreement + bias
   against these human labels) BEFORE it is used for anything.

## Verdict
validated_for_standalone_use = **False**;
forbidden_from_core_success_scoring = **True**.
The judge agrees with humans on clear cases but is lenient on token-order drift (a zero-agreement slice) and is fully order-dependent on close pairwise calls. It is therefore NOT validated for standalone use and is forbidden from core scoring; it may assist ONLY on the narrow fallback-quality question, outside its failure slice, with the bias mitigated.
