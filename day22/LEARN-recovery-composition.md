# LEARN — recovery policy composition

## Recovery is a conditional decision, not a bag of tricks

M1–M6 do not compete to become one universal recovery button. Each changes a
different failure path:

- M1 changes invalid structured output;
- M2 changes slow calls;
- M3 changes whether a failing provider is called;
- M4 changes who answers after a provider failure;
- M5 changes how much execution is allowed;
- M6 changes what happens after non-progress repeats.

The matrix confirms the design. M1 and M2 recover their transient target faults,
M4 recovers some F4 answers, M5 contains F6 resource consumption, and M6 recovers
transient F6 repetitions. Outside their target signals, the best case is usually
no effect. The worst case is a new failure.

## Composition has an order

A defensible recovery stack is:

```
M5 outer step/cost envelope
  → detect and classify the failure
    → select one narrow mechanism
      → validate recovered output
        → success, contained failure, or escalation
```

M5 belongs outside because every inner recovery—including retry and replan—can
consume steps and cost. It is the last structural guarantee when classification or
recovery is wrong.

The fault detector comes before recovery selection. Without that routing decision,
M1 wastes work on persistent or unrelated failures, M2 adds retry latency to faults
that cannot clear, and repetition detection can fire on valid repeated actions.

Validation comes after recovery. M4 can restore availability with an incorrect
fallback; only a correctness/quality check distinguishes recovery from a new silent
failure.

## Correct success, availability, and containment are different outcomes

The matrix carries all three because each mechanism optimizes a different one.

- **Correct success** means an acceptable answer was produced.
- **Availability** means an answer was produced, including wrong answers.
- **Containment** means no answer was produced, but the fault stopped within a
  known envelope.

M3 and M5 illustrate why this matters. A breaker can reduce calls without improving
correct success. A ceiling can turn an unbounded loop into a bounded terminal
failure without producing an answer. Calling either one “no improvement” loses the
reliability benefit; calling either one “success” overstates it.

M4 shows the opposite trap: availability improves even when some fallback answers
are wrong. Day 21's lesson remains active inside the Day-22 matrix.

## Why the clean controls are load-bearing

Fault-only datasets can measure recovery but cannot see recovery-induced
regression. Every matrix cell therefore includes six clean controls:

- ordinary short work;
- legitimate seven-step work;
- legitimate repeated pagination.

Those controls expose:

- five healthy requests blocked by M3 after clustered failures;
- twelve legitimate long plans stopped by M5;
- twelve legitimate repetitions stopped by M6.

They are paired outcome regressions, not hypothetical limitations.

## Cost and latency must be paired too

M1 and M2 recover 12 target-fault requests, but persistent cases spend their whole
retry budget for no success. M5 and M6 lower aggregate p95 latency because they
terminate F6 early, but their low latency includes prematurely aborted clean work.

That is why each cell stores the per-seed cost and latency difference, not merely
two independent averages. A low p95 is not automatically good if the mechanism
achieved it by refusing useful work.

## What the matrix says by fault

- **F1:** use bounded M1 after a structural validation signal.
- **F2:** use bounded M2 when a timeout signal says retry can plausibly help.
- **F3:** no M1–M6 mechanism repairs coherent semantic drift. Reject/re-ground.
- **F4:** M3 protects the provider; M4 restores answers; compose them, then check
  fallback quality.
- **F5:** no M1–M6 mechanism proves context correctness. Re-ground and validate.
- **F6:** M5 contains all execution; M6 can recover transient repetition inside it.

## Limits of the evidence

- The matrix is a deterministic benchmark with equal fault-family weighting, not a
  production traffic forecast.
- Costs and latency are virtual units intended for paired comparison.
- M3 and M4 are evaluated separately in the matrix; the recommended composition is
  supported by their complementary measurements and Day 20's combined experiment.
- M5/M6 thresholds deliberately include adversarial controls. Production values
  must be calibrated on real long-running and legitimately repetitive tasks.

The durable result is the policy shape: **bound globally, diagnose, recover
narrowly, validate afterward, and measure the failures recovery creates.**
