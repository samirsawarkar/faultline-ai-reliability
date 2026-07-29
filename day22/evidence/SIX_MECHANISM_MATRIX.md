# Day 22 — Six-mechanism recovery matrix

Every cell is paired against no recovery on the same 24 seeds (18 injected faults + 6 clean controls). `S` is correct-success rate; `ΔC` and `ΔL` are paired mean cost and latency changes; `H` is measured recovery-induced harm events.

| mechanism | F1 | F2 | F3 | F4 | F5 | F6 |
|---|---|---|---|---|---|---|
| M1 | S=0.75; ΔC=+1.5; ΔL=+20.5; H=6 | S=0.25; ΔC=+0.0; ΔL=+0.0; H=0 | S=0.25; ΔC=+0.0; ΔL=+0.0; H=0 | S=0.25; ΔC=+0.0; ΔL=+0.0; H=0 | S=0.25; ΔC=+0.0; ΔL=+0.0; H=0 | S=0.25; ΔC=+0.0; ΔL=+0.0; H=0 |
| M2 | S=0.25; ΔC=+0.0; ΔL=+0.0; H=0 | S=0.75; ΔC=+1.5; ΔL=+43.75; H=6 | S=0.25; ΔC=+0.0; ΔL=+0.0; H=0 | S=0.25; ΔC=+0.0; ΔL=+0.0; H=0 | S=0.25; ΔC=+0.0; ΔL=+0.0; H=0 | S=0.25; ΔC=+0.0; ΔL=+0.0; H=0 |
| M3 | S=0.25; ΔC=+0.0; ΔL=+0.0; H=0 | S=0.25; ΔC=+0.0; ΔL=+0.0; H=0 | S=0.25; ΔC=+0.0; ΔL=+0.0; H=0 | S=0.0417; ΔC=-1.2917; ΔL=-11.4583; H=5 | S=0.25; ΔC=+0.0; ΔL=+0.0; H=0 | S=0.25; ΔC=+0.0; ΔL=+0.0; H=0 |
| M4 | S=0.25; ΔC=+0.0; ΔL=+0.0; H=0 | S=0.25; ΔC=+0.0; ΔL=+0.0; H=0 | S=0.25; ΔC=+0.0; ΔL=+0.0; H=0 | S=0.75; ΔC=+0.75; ΔL=+9.0; H=6 | S=0.25; ΔC=+0.0; ΔL=+0.0; H=0 | S=0.25; ΔC=+0.0; ΔL=+0.0; H=0 |
| M5 | S=0.1667; ΔC=-0.0833; ΔL=-0.8333; H=2 | S=0.1667; ΔC=-0.0833; ΔL=-0.8333; H=2 | S=0.1667; ΔC=-0.0833; ΔL=-0.8333; H=2 | S=0.1667; ΔC=-0.0833; ΔL=-0.8333; H=2 | S=0.1667; ΔC=-0.0833; ΔL=-0.8333; H=2 | S=0.1667; ΔC=-4.5833; ΔL=-45.8333; H=2 |
| M6 | S=0.1667; ΔC=-0.0833; ΔL=-0.8333; H=2 | S=0.1667; ΔC=-0.0833; ΔL=-0.8333; H=2 | S=0.1667; ΔC=-0.0833; ΔL=-0.8333; H=2 | S=0.1667; ΔC=-0.0833; ΔL=-0.8333; H=2 | S=0.1667; ΔC=-0.0833; ΔL=-0.8333; H=2 | S=0.6667; ΔC=-4.5833; ΔL=-45.8333; H=2 |

## Aggregate outcome, cost, and latency (144 paired requests per mechanism)

| mechanism | correct success | availability | contained | answered wrong | mean cost | p95 latency | recoveries | regressions | measured harms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| no recovery | 0.25 | 0.625 | 0.0 | 0.375 | 3.2917 | 120 | — | — | — |
| M1 | 0.3333 | 0.5833 | 0.0417 | 0.25 | 3.5417 | 120 | 12 | 0 | 6 |
| M2 | 0.3333 | 0.7083 | 0.0417 | 0.375 | 3.5417 | 120 | 12 | 0 | 6 |
| M3 | 0.2153 | 0.5903 | 0.1042 | 0.375 | 3.0764 | 120 | 0 | 5 | 5 |
| M4 | 0.3333 | 0.75 | 0.0 | 0.4167 | 3.4167 | 120 | 12 | 0 | 6 |
| M5 | 0.1667 | 0.5417 | 0.2083 | 0.375 | 2.4583 | 60 | 0 | 12 | 12 |
| M6 | 0.25 | 0.625 | 0.125 | 0.375 | 2.4583 | 70 | 12 | 12 | 12 |

## Recovery-induced harms (none hidden)

- **M1:** 6 — {'wasted_repair_budget': 6}
- **M2:** 6 — {'wasted_timeout_retry_budget': 6}
- **M3:** 5 — {'false_open_blocked_healthy': 5}
- **M4:** 6 — {'silent_fallback_degradation': 6}
- **M5:** 12 — {'premature_step_ceiling': 12}
- **M6:** 12 — {'false_repetition_positive': 12}

M1/M2 spend retry budgets on persistent faults; M3 false-opens on healthy controls after clustered provider failures; M4 can turn an unavailable failure into an answered-but-wrong fallback; M5 cuts off legitimate long plans; M6 mistakes legitimate pagination for non-progress. These are measured effects, not footnotes.

## Composition conclusion

Detect first, then select the narrowest mechanism: M1 for F1, M2 for F2, M3+M4 for F4, M5 as an outer envelope, and M6 inside that envelope for F6. F3/F5 require semantic rejection/re-grounding; none of M1–M6 proves those answers correct.

Applying every mechanism to every request compounds false opens, premature ceilings, latency, cost, and repetition false positives.

Checkpoint 22 passed: **True**. Matrix fail-condition guard passed: **True**.
