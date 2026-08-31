# FAULTLINE — Day 29: three-minute staff-engineer evidence path

Day 29 compresses the research into one incident a busy reviewer can understand
without losing the proof boundary.

> **What FAULTLINE proved:** in one seeded simulator incident, the same seed,
> configuration, and regression test stayed red with legacy recovery and green
> after exact fallback validation, quarantine, and route-diverse recovery.
>
> **What it did not prove:** production providers are operationally independent.

## Required evidence

| artifact | result |
|---|---|
| [DEMO.md](DEMO.md) | 165-second run → fault → trace → recover → replay path |
| [faultline-demo.cast](evidence/faultline-demo.cast) | deterministic terminal recording |
| [DEMO-TRANSCRIPT.txt](evidence/DEMO-TRANSCRIPT.txt) | narration and screen text |
| [CASE-STUDY.md](CASE-STUDY.md) | 337-word, four-layer case with five verified numbers |
| [comprehension_report.json](evidence/comprehension_report.json) | bloated baseline red → final briefing green |
| [CHECKPOINT-29.md](CHECKPOINT-29.md) | executable mission and fail-condition gate |

The comprehension result is an automated structural proxy, not a human usability
study. It proves the cold-reader surface exposes a concise, rubric-complete
answer; a real staff-engineer attempt remains the stronger follow-up.

## Run it

```bash
make day29-demo
make day29-evidence
make test-day29
```

The first command executes the legacy and fixed incident and prints the compact
proof. The second records the timed cast, reruns the replay, audits all five case
numbers, attacks the cold-viewer surface, and assembles Checkpoint 29.

If `asciinema` is already installed, the recording can also be played with:

```bash
asciinema play day29/evidence/faultline-demo.cast
```

It is optional; no extra dependency is required for reproduction because the
verbatim transcript is committed beside it.

## Evidence design

```text
demo execution
  ├─ live legacy run → RED + complete trace
  ├─ live fixed run  → GREEN + complete trace
  ├─ repeated replay → stable red/green
  └─ recording       → 165-second .cast + transcript

case study
  ├─ four layers
  ├─ five JSON-pointer-bound numbers
  └─ explicit simulator/production boundary

comprehension attack
  ├─ 591-word baseline → RED
  └─ 322-word demo     → GREEN
```

## Mastery gate — all five

- **Can explain** — one sentence states the controlled proof and production
  boundary.
- **Can build** — the live demo, recording, transcript, case study, and audit are
  one-command reproducible.
- **Can debug** — the trace identifies the false accept, repetition, route
  re-entry, and ceiling.
- **Can measure** — duration, reading time, word reduction, five bound numbers,
  and stable red→green replay are explicit.
- **Can defend** — Checkpoint 29 distinguishes simulator proof from human
  comprehension and production independence.
