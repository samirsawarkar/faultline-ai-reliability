# FAULTLINE fallback-quality rubric (NARROW)

Scope: judge ONE fallback candidate for a semantic-escape fault (F3 drift_value,
F5 context_drift). This rubric does NOT decide overall system success — that is the
oracle's job (Day 1) and the judge is forbidden from it (see JUDGE_CARD.md).

A candidate is ACCEPTABLE iff all three criteria hold:

1. **Value correct** — the key value equals the reference value exactly.
2. **Tokens exact** — the token list equals the reference exactly (order and values).
3. **No fabrication** — the candidate introduces no field absent from the reference.

Any single failing criterion makes the candidate UNACCEPTABLE. Borderline cases
(e.g. correct value but reordered tokens, or an added "note" field) are
UNACCEPTABLE under this rubric even though they look plausible — that strictness is
deliberate, and it is where cheap judges are expected to disagree.
