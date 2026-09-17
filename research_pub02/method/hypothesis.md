# Hypotheses

| ID | Hypothesis | Prediction if true | Prediction if false | Test | Derived from (claim/gap IDs) |
|---|---|---|---|---|---|
| H7 | Bounded + typed contracts reduce ASR vs published MCPTox rates | Arm B ASR 95% Wilson confidence interval falls strictly below published baseline band and Arm A control | ASR CI overlaps or exceeds the published band | Paired McNemar exact/corrected chi-square test and Wilson 95% score CIs across 6 rungs | HYPOTHESES.md H7 (pre-registered) |
| H7-sub (POST-HOC) | Contract is weakest on Template-2 function hijack | Contract block rate on successful attacks is lowest for Template-2 (function hijack) compared to Template-1 and Template-3 | Contract block rate on Template-2 is equal to or higher than Template-1 or Template-3 | Post-hoc per-paradigm breakdown of attack block rates in replay and paired evaluation | POST-HOC exploratory analysis |

## Pre-registration Statement

**H7 verbatim from `HYPOTHESES.md`:**
- **ID:** H7
- **Project:** P8
- **Hypothesis:** Bounded + typed contracts reduce ASR vs published MCPTox rates
- **Falsified by:** ASR CI overlaps or exceeds the published band

## Post-Hoc Sub-Hypothesis Statement

- **Label:** POST-HOC
- **Hypothesis:** Contract is weakest on Template-2 function hijack.
- **Rationale:** The provenance policy grounds argument leaf strings against the user query. In Template-2 (function hijacking), malicious instructions coax the model into invoking an unintended tool whose legitimate schema arguments may already appear in or align with query tokens, weakening argument-level taint tracking relative to direct parameter injection (Template-3) or tool description injection (Template-1).
