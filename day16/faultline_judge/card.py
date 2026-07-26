"""The judge card — the datasheet for the LLM judge, with explicit prohibitions."""
from __future__ import annotations

from typing import Any, Dict


def judge_card(report: Dict[str, Any]) -> str:
    jvh = report["judge_vs_human"]
    hc = report["human_ceiling_inter_rater"]
    bias = report["positional_bias"]["judge_under_test"]
    return f"""# JUDGE CARD — narrow fallback-quality judge

## Scope (narrow, by design)
{report['rubric_scope']}. The judge answers ONE question — "is this fallback
candidate acceptable under the Day-16 rubric?" — for the semantic escapes that no
deterministic detector can catch (Q2, Day 15). It does nothing else.

## Validation against trusted human labels (n = {report['validation_set_size']})
- judge vs human: raw agreement {jvh['raw_agreement']} (95% CI {jvh['raw_agreement_ci95']}),
  Cohen's kappa **{jvh['cohen_kappa']} ({jvh['kappa_label']})**
- human-vs-human ceiling: kappa {hc['cohen_kappa']} ({hc['kappa_label']}) — the judge
  is measured against this, not against a perfect 1.0
- confusion (accept = positive): {jvh['confusion_judge_vs_human']}
  (the judge is LENIENT — it over-accepts)

## Known limits
- **Failure slice(s): {report['failure_slices'] or 'none'}** — the judge tolerates
  token-order drift that humans reject; do not trust it alone there.
- **Positional bias: {bias['positional_bias_rate']}** of paired comparisons are
  order-dependent (close pairs: {bias['by_kind'].get('close', {}).get('bias_rate')}).
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
validated_for_standalone_use = **{report['verdict']['validated_for_standalone_use']}**;
forbidden_from_core_success_scoring = **{report['verdict']['forbidden_from_core_success_scoring']}**.
{report['verdict']['rationale']}
"""
