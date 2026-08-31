# FAULTLINE in 2:45 — one incident from run to replay

> **What FAULTLINE proved:** In one seeded simulator incident, the same seed, configuration, and regression test stayed red with legacy recovery and green after exact fallback validation, quarantine, and route-diverse recovery; this does not establish provider independence in production.

The live command is `make day29-demo`. The [recording](evidence/faultline-demo.cast)
and [verbatim transcript](evidence/DEMO-TRANSCRIPT.txt) are generated from the
same executable incident.

## 00:00 · RUN

Fix one incident, seed, configuration, and user-visible regression. The test
requires a correct visible answer, no wrong visible answer, and the declared
resource ceilings to hold. The legacy policy starts red.

## 00:24 · FAULT

The primary times out twice. Fallback preserves the headline value but shifts the
context tokens. A narrow judge accepts its known failure slice. Verification
repeats without changing evidence, the same route re-enters, and the cost ceiling
blocks final synthesis. No wrong answer escapes, but the user receives no correct
service.

## 00:58 · TRACE

The complete trace links the false accept to repetition, route re-entry, and the
terminal ceiling. Every regression reference resolves. The root cause is not
“the model failed”; the controller gave a narrow judge authority inside its
documented blind spot.

## 01:34 · RECOVER

Run the same incident with three controls: compare fallback tokens exactly,
quarantine the rejected provider and fingerprint, and require a route with
independent context. The fallback is rejected, the route changes, and the same
regression turns green.

## 02:12 · REPLAY

Repeat both policies under the same seed, configuration, and test. Legacy remains
red; fixed remains green; the traces remain complete. That is the proof:
trace-linked corrective controls changed the user outcome and stayed fixed.

**Boundary:** this is deterministic evidence for one configured simulator
incident. A production claim still needs dependency mapping, measured guard
error, and live fault drills.

Continue with the [one-page case study](CASE-STUDY.md), then inspect the
[full Q1–Q5 article](../day28/ARTICLE.md) only if you need the wider argument.
