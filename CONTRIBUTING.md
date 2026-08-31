# Contributing to FAULTLINE

FAULTLINE welcomes small, evidence-backed improvements. A contribution is ready
when another reader can reproduce both the problem and the claimed outcome
without private context.

## Before opening a change

1. Describe the user-visible failure, not only the component symptom.
2. State the seed, configuration, expected terminal state, and budget envelope.
3. Keep the evaluator independent from the mechanism being evaluated.
4. Prefer the smallest change that makes one claim testable.

For behavior changes, open an issue first when the proposed outcome definition
or policy boundary is ambiguous.

## Local workflow

```bash
make venv
make reproduce-fast
```

Run the focused day suite while iterating, then run the full gate before review:

```bash
make test-day25
make reproduce
```

Use the day target that owns your change; Day 25 is only an example.

## Evidence required by change type

| Change | Minimum evidence |
|---|---|
| New fault | Seeded trigger, severity, complete trace, terminal label, and replay stability |
| New detector | Frozen labels, confusion matrix, false-negative examples, slice metrics, and intended authority |
| New recovery policy | No-recovery control, paired seeds, correct success, wrong answers, cost, latency, uncertainty, and a stress attack |
| Incident fix | Before/after traces, same-seed red→green test, repeated-process stability, and residual risk |
| Headline claim | Committed result, generator, reproduction command, JSON binding, and explicit limitation |

Do not report availability alone as recovery success. Do not use a detector or
judge as its own correctness oracle.

## Pull request checklist

- [ ] The user-visible outcome and operating envelope are explicit.
- [ ] New behavior has a failing-before, passing-after test where applicable.
- [ ] Compared policies use paired seeds.
- [ ] Cost, latency, wrong answers, and uncertainty are measured.
- [ ] Traces contain enough provenance to reconstruct the decision.
- [ ] Documentation links to the result and generator.
- [ ] `make reproduce` passes without uncommitted evidence drift.
- [ ] Limitations and evidence that would reverse the decision are stated.

## Review standard

Reviews focus on causal attribution, evaluator independence, budget enforcement,
replayability, and claim traceability. Style improvements are welcome, but they
do not substitute for paired evidence.
