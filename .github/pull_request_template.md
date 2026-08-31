## User-visible problem

<!-- Describe the outcome a user sees. Do not stop at the component symptom. -->

## Decision and operating envelope

<!-- State the proposed decision, seed/config, correctness boundary, budgets,
and evidence that would reverse it. -->

## Paired evidence

<!-- Link the control/candidate result, uncertainty, cost, latency, wrong-answer
measurement, trace, and generating command. -->

## Failure and replay

<!-- Link the initiating fault, propagation chain, before/after trace, and
red→green regression when behavior changes. -->

## Limitations

<!-- State what this change does not prove and any unmeasured production risk. -->

## Verification

- [ ] Focused tests pass.
- [ ] Compared mechanisms use the same seeds.
- [ ] Evaluator labels are independent from the policy under test.
- [ ] Cost, latency, wrong answers, and uncertainty are measured.
- [ ] `make reproduce` passes with no evidence drift.
- [ ] Documentation links every headline to a committed result and generator.
