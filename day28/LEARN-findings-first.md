# LEARN — findings-first writing and standalone figures

## The article is an argument, not a diary

A chronological report says what was built on each day. A findings-first article
starts with the question a reader must decide, then gives the strongest result,
its uncertainty, and the condition that limits it. Implementation appears only
after the reader understands why the measurement matters.

For FAULTLINE, the argument has one dependency chain:

```text
depth changes failure exposure
  → detection must be measured by escape type
  → retries need correlation-aware ceilings
  → fallback needs an answer-quality measure
  → policy choice needs correctness, cost, latency, uncertainty, and attacks
```

This is not a causal chain estimated from one population. It is a design argument
assembled from five experiments with distinct populations.

## Finding, interpretation, recommendation

- A **finding** reports an observed comparison with its population and
  uncertainty.
- An **interpretation** explains the mechanism consistent with the traced
  evidence.
- A **recommendation** adds an explicit decision rule and operating envelope.

The publication ledger treats all three as claims. Method paragraphs are
registered too, but findings, interpretations, and recommendations must also
name an honest limitation.

## Standalone caption contract

A figure caption should answer five questions without nearby prose:

1. What population or seed set was measured?
2. What is being compared?
3. What outcome and uncertainty are shown?
4. What is the principal reading?
5. What limitation prevents the obvious overclaim?

The title supplies the memorable idea. The caption supplies the evidence
contract. The plotted marks should not carry every caveat; the caption should.

## Claim-to-result audit

A hyperlink is useful for a person but weak as an automated proof. Day 28 binds
the exact rendered token to:

```text
artifact path + JSON pointer + display format
```

The audit also checks that every source is a Git blob at the current revision.
This prevents a working-tree scratch result from supporting publication prose.
It then requires one marker for every substantive paragraph, five source-linked
figures, identical captions in both publication surfaces, and at least one
limitation for every non-method claim.

## Defending a conditional finding

The strongest defensible sentence is not the broadest one. It names:

- the configured population;
- the user-visible outcome;
- the comparator;
- the cost and latency dimensions;
- the uncertainty rule;
- the attack that withdraws the recommendation.

That structure turns “it worked” into a decision another reviewer can reproduce,
challenge, and reverse.
