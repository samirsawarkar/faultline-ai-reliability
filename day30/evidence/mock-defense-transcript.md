# Recorded skeptical staff-level mock defense

Format: ten closed-book questions. The candidate answers from the evidence
model—decision, measured result, tradeoff, limitation, and reversal trigger—
without opening implementation code.

This recording demonstrates that complete evidence-led answers can be delivered
aloud. It is synthetic narration of the prepared defense, not an empirical test
of the repository author's unaided speaking performance.

## 1. Why not multiply single-hop reliability?

**Interviewer:** Your first-hop success is 0.972. Why is p to the n not a sufficient planning model?

**Candidate:** I rejected the exchangeable-hop assumption because the measured end-to-end process diverged materially: at eight required hops success was 0.288 while p to the n predicted 0.796765, and the naive curve first left the measured interval at hop 3. The tradeoff is more instrumentation and conditional estimates, with fewer runs reaching deep hops. This is a configured decay simulator, not a production rate. I would reverse the planning model only after production per-hop conditional reliability shows stable exchangeability across depth and task slices.

## 2. Why inspect detector misses instead of reporting F1?

**Interviewer:** Precision is perfect. Why not ship the detector and tune it later?

**Candidate:** Perfect precision did not make the detector safe: on 44 labelled examples recall was 0.615385 and all 10 false negatives mattered. Six misses were threshold-reducible, but four were semantic escapes, so one threshold could not close the gap. The tradeoff is abstention and extra review on ambiguous cases. This is a small synthetic labelled set with wide slice intervals, not a production guarantee. I would promote the detector only after a larger target-population evaluation preserves false-negative visibility and meets a predeclared per-slice recall floor.

## 3. Why exclude the semantic judge from core success?

**Interviewer:** A semantic judge catches failures deterministic checks miss. Why forbid it from the success label?

**Candidate:** The judge cannot validate itself. On 24 examples it reached raw agreement 0.75 and kappa 0.5, produced six false accepts, and had zero agreement on the borderline-token slice. I therefore use it only as an advisory signal outside that slice and never in core success scoring. The tradeoff is lower automated coverage in exchange for label independence. The validation set is small and synthetic. I would reverse the exclusion only after independent human labels show calibrated per-slice performance, including the current failure slice, at a predeclared threshold.

## 4. Why do retry caps change under correlation?

**Interviewer:** If three attempts work under independent faults, why not keep three during an outage?

**Candidate:** A retry targets another draw; correlation removes that benefit while retaining the work. Under independent faults the last point inside the configured ceilings was K equals 3, with success 0.76 and 1.9 times amplification. Under correlated faults it moved to K equals 2; K equals 3 amplified attempts 2.37 times for only 0.415 success. The tradeoff is giving up some recoverable requests to protect the shared system. These are virtual-latency simulator ceilings. I would raise the cap only when live correlation and marginal-success measurements stay inside explicit amplification and tail-latency budgets.

## 5. Why is availability not the fallback outcome?

**Interviewer:** Fallback reached 100 percent availability. What more does an operator need?

**Candidate:** The operator needs the user outcome and the route provenance. Across 120 paired requests, fallback raised availability from 0.6667 to 1.0 while strict quality among answered requests fell from 1.0 to 0.75; 30 of 40 fallback answers were silently degraded. The tradeoff is that quality gates may reject an answer and lower visible availability. The outage schedule and answer mix are constructed simulator conditions. I would relax a gate only after production-labelled fallback slices show the resulting wrong-answer bound remains inside the declared risk budget.

## 6. Why compose recovery in a fixed order?

**Interviewer:** Why not enable all six recovery mechanisms and let each handle its own fault?

**Candidate:** Recovery mechanisms create faults of their own. The six-mechanism matrix enumerated 47 induced harms, including wrong available answers, false opens, and premature ceilings. I therefore compose an outer step-and-cost envelope, then detection, narrow recovery, quality validation, and finally success, containment, or escalation. The tradeoff is more contained requests when evidence is insufficient. The matrix uses 24 paired synthetic seeds per cell, not production traffic. I would change the order only after paired mechanism-by-fault evidence measures every newly induced failure under the new composition.

## 7. Why constrain before optimizing efficiency?

**Interviewer:** Why not choose one weighted utility and optimize it directly?

**Candidate:** No stakeholder supplied a defensible exchange rate between a wrong answer, money, and waiting. I first required the success lower bound, wrong-answer upper bound, mean-cost upper bound, and p95-latency upper bound to pass; only P1 and P4 were eligible. Among them P4 gained 0.095 correct success and its success-per-cost advantage was 0.0485 with a paired 95 percent interval from 0.0319 to 0.0664. The tradeoff is refusing a single convenient rank. This is simulator utility, not production preference. I would use a weighted objective only after accountable stakeholders publish stable weights and loss meanings.

## 8. Why call the winning policy only an upper bound?

**Interviewer:** P4 wins cost and latency efficiency. Why not recommend it for production?

**Candidate:** P4 is a reference upper bound because it receives simulator-truth retryability and a strict simulator-oracle fallback guard. In the base envelope it reached 0.9325 correct success at mean cost 1.4656 and p95 latency 50.0, but success fell to 0.695 under worse severity and 0.575 under tight budgets. The tradeoff is a useful design target without a deployment promise. The synthetic oracle removes classifier errors that production must pay for. I would recommend deployment only after replacing both oracle signals with measured components and rerunning the paired selection and stress attacks.

## 9. Why call the cascade causal?

**Interviewer:** Your trace is just temporal order. How can you call the cascade causal?

**Candidate:** The production objection is correct: temporal order alone is not causality. The narrower claim is intervention-informed simulator causality. One serialized seed, 2026080207, and one full configuration inject only the primary latency fault; the expected labelled chain and trace digest repeat across 20 runs. The tradeoff is strong reproducibility inside a controlled model rather than broad realism. Hidden production confounders and route dependence remain unmeasured. I would transfer the causal claim only after targeted interventions or natural experiments break and restore the same links in production.

## 10. What proves a fix stays fixed?

**Interviewer:** A before-and-after demo can be staged. What makes your postmortem fix credible?

**Candidate:** The intervention is the policy version; the seed, configuration, regression ID, predicate, and trace assertions stay fixed. For incident INC-25-001, legacy recovery remained red and the fixed policy green across 20 repetitions; latency changed from 98 to 94 while cost remained 11. The tradeoff is a narrow regression guarantee, not proof against every future incident. The route-diversity assumption is still simulated and may fail operationally. I would reopen the incident if a production replay changes the digest, violates the original predicate, or shows the supposedly independent route shares a failure domain.

## Closing statement

FAULTLINE does not prove a universal recovery policy. It proves a decision
discipline: measure correct user-visible outcomes, pair comparisons, preserve
provenance, enforce budgets, attack the winner, and withdraw the recommendation
when the operating envelope changes.
