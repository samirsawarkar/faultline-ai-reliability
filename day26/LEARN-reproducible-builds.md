# LEARN — reproducible builds and research CI

## Reproducibility has layers

“The code is on GitHub” is not a reproduction contract. A result depends on:

- source revision;
- runtime and operating-system image;
- direct and transitive packages;
- seeds and dataset version;
- locale, hash order, and clocks;
- the exact command;
- the definition of success.

A build can be reproducible while the experiment is not, and an experiment can
be deterministic inside an unreproducible environment. Day 26 checks both.

## Pin identities, not compatibility ranges

Compatible ranges are useful for libraries that promise ecosystem flexibility.
They are weak evidence for a research release because a future resolver can
select different code.

Day 26 pins:

- the image manifest digest, not only a mutable tag;
- Python patch versions, not only minor versions;
- transitive packages, not only top-level requirements;
- GitHub Actions commit SHAs, not moving major tags.

Pins trade automatic upgrades for controlled upgrades. Security and compatibility
updates become explicit experiments with reviewable evidence diffs.

## A container is necessary but not sufficient

A Dockerfile improves isolation, but it can still be non-reproducible if it:

- starts from an unpinned base;
- upgrades packages to “latest”;
- copies a host virtual environment;
- depends on wall time or network data during the experiment;
- runs as root and hides permission assumptions;
- builds successfully without executing the research.

The Day 26 image runs the complete reproduction during `docker build`. Packaging
cannot be green while the research gate is red.

## Separate build inputs from result evidence

Inputs are versioned source, pins, seeds, and frozen data. Outputs are result
artifacts and reports. A reproduction command should regenerate outputs from
inputs and compare them byte-for-byte where the model is deterministic.

Wall-clock duration, host paths, and machine IDs are deliberately absent from
committed result JSON because they create noise without supporting the claim.

Even a seeded experiment can vary at the last floating-point bit when different
Python versions call different platform math libraries. Derived statistics must
therefore declare their evidence precision. Day 26 canonicalizes McNemar values
to 15 significant digits: enough precision for the analysis, but not enough to
mistake machine-specific rounding noise for a scientific result.

## Research CI is more than unit tests

Unit tests answer whether local functions satisfy contracts. Research CI must
also ask:

- Does the frozen evaluation produce the same result ID and metrics?
- Do representative experiments regenerate identical artifacts?
- Are headline claims still equal to their source JSON values?
- Does the clean environment reproduce?
- Did any committed evidence change unexpectedly?

These checks catch silent scientific drift that ordinary code tests miss.

## Fast and full profiles serve different purposes

The full profile provides release confidence. The fast profile provides feedback
speed. A credible fast subset should cross important system boundaries rather
than merely choose the shortest unit tests.

Day 26 samples deterministic simulation, statistical quality measurement, and
trace/replay recovery. The clean image runs the full profile.

## Traceability is executable documentation

A prose link says “the result is somewhere over there.” A traceability record
states:

`README text → typed value → JSON pointer → artifact → generator → command`

The chain can be audited. If the artifact changes and the README does not, CI
turns red. If someone adds a result row without registering it, CI turns red.

## Release tags are conclusions

A release-candidate tag should point to the exact commit whose clean reproduction
passed. Tagging before the reproduction inverts the evidence relationship: the
claim exists before its proof.

The safe order is:

1. freeze pins and evidence;
2. run host gates;
3. build and attest the clean image;
4. verify the final checkpoint;
5. commit the proven state;
6. tag that commit;
7. let remote CI independently repeat the checks.

## Limits

Digest pinning does not guarantee long-term registry availability. Containers do
not emulate all CPU, kernel, or network behavior. Deterministic simulators do not
quantify production distribution shift.

Durable releases should archive source, dependency artifacts, and result bundles
in addition to preserving the Git tag.
