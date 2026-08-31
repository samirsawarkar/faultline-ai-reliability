# Evidence-led launch positioning

## One sentence

FAULTLINE is a reproducible reliability workbench that tests whether AI recovery
improves correct user-visible outcomes—not merely availability—inside explicit
cost and latency limits.

## Who should see which evidence

| audience | first artifact | question to invite |
|---|---|---|
| staff/platform engineer | [Day 29 demo](../day29/DEMO.md) | Can you state the proof and its production boundary? |
| reliability researcher | [Day 28 article](../day28/ARTICLE.md) | Which assumption or uncertainty treatment would you challenge? |
| observability maintainer | [Day 23 trace narrative](../day23/evidence/INCIDENT_NARRATIVE.md) | Which recovery and provenance fields should be portable? |
| evaluation maintainer | [Day 16 judge report](../day16/evidence/agreement_report.json) | Is the forbidden-use boundary strict enough? |
| recovery-framework maintainer | [Day 22 matrix](../day22/evidence/SIX_MECHANISM_MATRIX.md) | Which induced failure is missing from the composition? |

## Claims to avoid

- “Self-healing AI.”
- “Production-proven recovery.”
- “The semantic judge guarantees quality.”
- “P4 is the universal best policy.”
- “A trace proves causality.”

## Launch rule

Lead with one falsifiable result and one limitation. Ask for one specific kind of
review. Stop after two high-fit messages until their response shows whether the
evidence is useful or merely well packaged.
