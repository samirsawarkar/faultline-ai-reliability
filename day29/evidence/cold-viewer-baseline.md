# Cold-viewer attack fixture — the version with too much context

This deliberately bloated fixture preserves the kind of chronological detail
that accumulated during the research program. It is not the publication surface.
The comprehension gate should reject it because the viewer has to infer the main
proof from implementation history.

FAULTLINE began by constructing a deterministic document-grounded task and an
oracle that separated schema validity from answer correctness. It added a bounded
agent loop, cost and step ceilings, a provider interface, traces with parent and
child links, fault injection, and a series of detector experiments. Later modules
split the six fault families into deterministic and semantic groups, measured
per-class recall, validated a narrow semantic judge, and audited subgroup
contradictions. This background matters to the research program but it delays the
incident answer a busy staff engineer needs.

The cascade incident starts after a primary provider exceeds its timeout. A retry
also times out, which opens a breaker and activates fallback. The fallback has the
correct headline value but stale context tokens. A narrow semantic judge sees the
candidate. The judge had previously shown moderate agreement on a narrow
validation set and a known failure on token-order changes. In the cascade, the
judge accepts the stale fallback. The agent then verifies the same evidence more
than once, replans without excluding the failed route, and calls the same
secondary provider with the same fingerprint. The global cost ceiling prevents
final synthesis.

There are several mechanisms involved. Retry is useful on independent transient
failures but can become amplification when failures are correlated. Breakers
contain provider pressure but may send requests to a lower-quality route.
Fallback raises availability while changing the answer-quality distribution.
Repetition detection can stop a loop but only if recovery changes either the
evidence or the route. A budget ceiling limits blast radius but can also end a
request without correct service. All of those ideas are relevant, yet presenting
them before the incident result makes the proof hard to restate.

The corrective path applies a deterministic token comparison, rejects stale
fallback, quarantines the provider and fingerprint, and selects a trusted route
with independent context. A final synthesis returns a correct visible answer
within the configured ceilings. The regression evaluates correct visibility,
wrong-answer visibility, cost, and steps. The legacy and fixed policies are
executed repeatedly with aligned configuration. Cross-process checks also vary
the Python hash seed to establish deterministic replay.

The incident report includes a timeline, impact, detection, root cause,
contributing factors, corrective actions, before and after outcomes, trace
digests, run digests, regression references, and stability summaries. Separate
artifacts store the full before and after traces. The broader Q1–Q5 article also
explains depth, detector misses, retry crossover, fallback degradation, and policy
selection. A reader can follow all of those links, but this draft does not tell
them which one sentence to retain.

The production boundary is also distributed across the material. The simulation
does not establish that two providers have independent infrastructure, data
freshness, or failure modes. The narrow judge is not validated for standalone
success scoring. The observed intervals describe configured simulator
populations, not model-form uncertainty or production shift. Live dependency
mapping and fault drills remain necessary. Those caveats are important, but in
this fixture they arrive after too much background and are not attached to a
single explicit proof statement.

The fixture therefore contains accurate evidence but fails the staff-engineer
task. It asks the viewer to synthesize architecture, experiment history, trace
mechanics, statistical boundaries, and a deployment caveat before they can
answer the basic question: what did FAULTLINE prove?
