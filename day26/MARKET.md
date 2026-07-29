# MARKET — evidence a technical buyer can rerun

## The gap

AI reliability reports often separate the persuasive artifact from the runnable
system. Numbers appear in a README or deck, while scripts, seeds, package
versions, and exact outputs are left for the buyer to reconstruct.

## Day 26's evidence contract

A defensible research release should let a reviewer:

1. see the important questions and answers immediately;
2. click each answer into machine-readable evidence;
3. find the exact generating script beside it;
4. reproduce locally with one command;
5. reproduce from a digest-pinned clean image;
6. inspect every runtime, dependency, seed, and CI-action pin;
7. observe CI rerun tests, evaluation, experiments, claim checks, and the
   container build;
8. identify the exact release-candidate commit.

## Buyer value

The deliverable can support vendor evaluation, internal model-governance review,
incident regression, and architecture decisions because evidence is portable
rather than presenter-dependent.

## Defensible claim

> The release candidate binds each headline number to a typed result value and
> generator, reproduces the research through host and clean-container commands,
> and checks the same contract continuously.

It is not:

> A deterministic simulator and container prove production behavior.

The evidence proves the repository's stated experiments. Live workload shift,
provider dependence, infrastructure timing, and long-term artifact availability
remain separate operational questions.
