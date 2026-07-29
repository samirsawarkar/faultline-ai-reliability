# MARKET — an incident artifact an operator can actually defend

## The gap

Many incident products provide a timeline and an AI-written summary. The hard
questions remain unanswered:

- Which fault initiated the incident?
- Which recovery action propagated it?
- Can another engineer reproduce the same chain?
- Does every causal claim point to trace evidence?

Day 23 packages those answers into one portable incident skeleton.

## Evidence contract

A buyer should require:

1. seed/input and complete configuration;
2. immutable configuration, incident, and trace digests;
3. labelled root cause, propagation, and containment events;
4. exact trace references for every causal node;
5. repeated and cross-process replay;
6. explicit distinction between recovered, contained, available, and correct.

The deliverable is useful for incident review, regression tests, vendor
comparisons, and tabletop exercises because the same incident can be regenerated
instead of merely screenshotted.

## Defensible claim

The market claim is:

> One configured simulator incident can be reproduced exactly, reconstructed from
> complete traces, and defended through a trace-referenced causal graph.

It is not:

> A single production trace proves causality.

Production causality still needs interventions, counterfactual comparisons, and
confounder analysis. Preserving that boundary is what makes the incident skeleton
credible.
