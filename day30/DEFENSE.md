# FAULTLINE staff-level defense guide

Use this as an oral drill, not a reading script.

For each prompt, answer in this order:

1. **Decision** — say what FAULTLINE chose.
2. **Evidence** — give the smallest decisive comparison.
3. **Tradeoff** — name what the choice costs.
4. **Boundary** — say what the experiment did not establish.
5. **Reversal** — state the evidence that would change the choice.

## Ten prompts

1. Why not multiply single-hop reliability?
2. Why inspect detector misses instead of reporting F1?
3. Why exclude the semantic judge from core success?
4. Why do retry caps change under correlation?
5. Why is availability not the fallback outcome?
6. Why compose recovery in a fixed order?
7. Why constrain before optimizing efficiency?
8. Why call the winning policy only an upper bound?
9. Why call the cascade causal?
10. What proves a fix stays fixed?

The full interviewer/candidate record is
[mock-defense-transcript.md](evidence/mock-defense-transcript.md), and the exact
evidence bindings and red→green scores are in
[defense_report.json](evidence/defense_report.json).

## Closing answer

FAULTLINE does not prove one universal recovery recipe. It proves a decision
discipline: measure correct user-visible outcomes, pair comparisons, preserve
provenance, enforce budgets, attack the winner, and withdraw the recommendation
when the operating envelope changes.
