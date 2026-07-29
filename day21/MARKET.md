# MARKET — what Q4 changes for an availability buyer

## The buyer's hidden risk

Fallback is usually sold as an availability feature: when the primary fails, the
system still returns an answer. Q4 shows why an uptime-only acceptance test is
insufficient. A system can meet a 100% response SLO while delivering a materially
worse answer mix.

In the measured scenario, fallback:

- restores availability from 0.6667 to 1.0;
- lowers strict quality among delivered answers from 1.0 to 0.75;
- sends 30 silently degraded answers;
- still improves strict-quality service coverage from 0.6667 to 0.75.

That last line matters commercially. The finding is not “fallback has no value.”
It is “fallback value cannot be priced or operated from uptime alone.”

## A procurement-ready acceptance test

Ask a fallback vendor for these metrics on paired production-like requests:

1. availability with and without fallback;
2. oracle or human-rubric correctness among answered requests;
3. acceptable-answer service rate over all requests;
4. fallback rate and provenance completeness;
5. fallback-only quality acceptance with uncertainty;
6. detector precision, recall, and every known failure slice.

The contract should include a fallback quality budget beside the availability SLO.
For example: alert when fallback share rises, when quality rejection crosses a
threshold, or when the audit sample's lower confidence bound breaches the agreed
floor.

## What cannot be claimed from this artifact

The included judge is not a standalone quality oracle. Its κ is 0.5 against a
human ceiling of 0.8, pairwise decisions show positional bias, and token-order
drift is a known blind spot. It is used only for pointwise fallback alerts and is
forbidden from core success scoring.

Any market claim should therefore say “quality monitored with a characterized
detector plus oracle/human audit,” not “LLM-judged quality guaranteed.”
