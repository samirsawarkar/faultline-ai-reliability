# LEARN — blameless postmortems and system root cause

## The purpose is durable learning

A postmortem is not a story about who last touched the system. It is an
explanation of how normal actions, incentives, controls, and assumptions combined
to produce an unwanted outcome—and how the system will make that outcome less
likely or less harmful next time.

“Blameless” does not mean consequence-free or vague. It means the report asks:

- What information was available at decision time?
- Why did the action look reasonable under that information?
- Which control allowed one local failure to propagate?
- What system change can be tested?

## Keep the sections distinct

### Timeline

The timeline states observed events and supporting trace references. It should not
smuggle causal language into chronology. “B followed A” is weaker than “A caused
B.”

### Impact

Impact describes what users or the system lost: correct answers, service,
latency, cost, or trust. Containment is part of impact, not success. Day 25's
first incident suppresses a wrong answer but still fails to return a correct one.

### Detection

Detection records the signal that made the incident visible and its delay. It
should also name blind spots. A budget alarm detects termination; it does not
necessarily detect the earlier semantic failure that consumed the budget.

### Root cause

A useful root cause is a controllable system condition that explains the incident
and predicts a counterfactual:

> The narrow judge was granted authority inside its documented failure slice.

If removing that condition breaks the causal chain, it is actionable. “The model
was wrong” and “operator error” are labels, not explanations.

### Contributing factors

Complex incidents rarely have one sufficient cause. Correlated providers, missing
route diversity, deadline-infeasible scheduling, weak observability, and budget
placement can each make the outcome more likely or more severe.

Calling them contributing factors preserves causal structure without forcing an
artificial single culprit.

## Five whys: useful, but not a proof

Repeated “why?” questions can move from symptom to system, but they tend to
produce one linear chain and stop wherever the interviewer chooses. Real systems
branch.

Use five-whys as a prompt, then verify the proposed edges with traces,
counterfactuals, or interventions. Day 25 changes one policy version while
holding seed, configuration, and regression fixed.

## Action items need observable completion

Weak action:

> Improve fallback reliability.

Strong action:

> Reject non-exact context tokens, quarantine the provider/fingerprint, and prove
> that the same seeded regression returns a correct answer within cost 12 and
> step 9.

The strong action names the control, expected outcome, envelope, and test.

## What red → green actually proves

A credible regression flip holds constant:

- incident input and seed;
- environment configuration;
- outcome predicate;
- measurement method.

Only the fix changes. The legacy policy must fail the test, or the regression
never demonstrated sensitivity to the incident. The fixed policy must pass, or
the action did not address the user outcome.

Repeated replay adds the “stays fixed” claim. Fresh processes and hash-seed
variation protect against accidental interpreter-state or ordering dependence.

## Avoid test-shaped fixes

A fix can make a test green without improving the system:

- weakening the expected result;
- changing the seed;
- increasing the budget until the incident disappears;
- suppressing the error while still returning no answer;
- mocking the failing component out of the path.

Day 25 prevents these shortcuts by comparing the same regression ID, seed, and
configuration and by requiring a correct visible outcome under the original
envelope.

## Root cause is proportional to evidence

Traces show sequence and component state. Deterministic replay shows that the
same inputs reproduce the chain. An intervention that removes one condition
strengthens a causal claim inside the simulator.

Production claims remain narrower:

- providers believed independent may share infrastructure;
- exact reference checks may be unavailable;
- hedging can amplify real provider load;
- concurrency introduces timing distributions absent from virtual time.

A strong postmortem states these boundaries and schedules the next measurement.

## Review checklist

- Is user impact quantified?
- Does every timeline event cite evidence?
- Are detection and root cause separated?
- Is the root cause a system condition rather than a person?
- Are contributing factors preserved?
- Does each corrective action name an enforceable control?
- Does the same test fail before the fix?
- Does it pass after the fix under the same envelope?
- Do repeated and fresh-process replays stay green?
- Are remaining production uncertainties explicit?
