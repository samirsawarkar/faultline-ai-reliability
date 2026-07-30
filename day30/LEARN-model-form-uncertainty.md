# Learn — model-form uncertainty

The weakest baseline defense answer was Q1. It said later hops could be harder,
but did not distinguish parameter uncertainty from model-form uncertainty.

Parameter uncertainty asks whether the first-hop success estimate is precise.
More first-hop trials can narrow that interval.

Model-form uncertainty asks whether multiplying that estimate is the right
structure at all. No amount of first-hop precision repairs an exchangeability
assumption when later conditional success changes with depth.

FAULTLINE exposed the distinction by comparing three objects:

- naive `p₁ⁿ`;
- measured end-to-end success;
- the product of measured conditional per-hop reliability.

The naive curve first left the measured interval at hop 3. At hop 8, it predicted
0.796765 while the measured rate was 0.288. The corrected conditional model
tracked the measurement because it admitted non-exchangeable later hops.

The defense rule is concise: state the assumption, show the residual pattern
that breaks it, name the population, and specify evidence that would restore
it. “The estimate might be noisy” is not an answer when the model structure is
wrong.
