# CHECKPOINT-20 — M3/M4: circuit breaker + provider fallback

**Mission.** Restore availability without hiding failures or blocking healthy
traffic.

**Fail condition.** Breaker transitions or fallback provenance cannot be traced. —
**Not triggered.**

## What was built

- **M3 circuit breaker** — CLOSED/OPEN/HALF_OPEN with a rolling-window failure
  threshold, cooldown, and half-open trials; every transition recorded as
  `{from, to, reason, tick}`.
- **M4 provider fallback** — primary → secondary → degraded chain; every response
  carries provenance (`served_by`, `is_fallback`, `is_degraded`), mirrored into a
  Day-4 trace.
- **A stream runner** (with a true no-breaker baseline) and a three-way paired study.

9 tests gate it; three evidence artifacts prove it.

## Traceability (the fail condition, refused)

`transitions_trace.json` records a full cycle on the canonical outage — including a
failed half-open trial mid-outage:

```
[t22] closed→open (failure_threshold) → [t32] open→half_open (cooldown_elapsed)
→ [t32] half_open→open (half_open_failed) → [t42] open→half_open → [t43] recovered
```

Every one of the 60 requests is in the Day-4 trace with its provenance; a test asserts
both the transition log and per-request provenance are complete.

## Restore availability, don't hide, don't block (paired study)

| config | availability | primary calls | healthy blocked |
|---|---|---|---|
| naive (no breaker/fallback) | 0.667 | 60 | 0 |
| breaker only | 0.633 | 42 | 2 |
| breaker + fallback | **1.00** | 42 | 2 |

- Breaker **saves 18 calls** to the failing primary (storm protection) — honestly, at
  a small availability cost on its own.
- Fallback **restores availability to 1.0** (+0.333); McNemar p ≈ 2e-6.
- **Not hiding:** the fallback-failure attack serves 60 degraded answers at 1.0
  availability with 0 unanswered — every degraded answer flagged.
- **Not blocking healthy traffic:** a tuned breaker blocks **0** healthy calls on
  isolated blips (a twitchy one blocks 25).

## Attacks

- **False opens:** twitchy (threshold 1) blocks 25 healthy calls; tuned (3-of-5) blocks 0.
- **Flapping:** eager 21 transitions → damped 7 (longer cooldown + higher success-threshold).
- **Fallback failure:** primary + secondary down → degraded keeps availability 1.0, 0 hidden.

## Mastery gate — all five

- **Explain** — `LEARN-breaker-degradation.md`: the state machine, tuning's two failure
  modes, and graceful degradation without hiding.
- **Build** — `faultline_breaker/`: breaker, fallback chain, runner.
- **Debug** — `transitions_trace.json`: timeline + per-request provenance + trace.
- **Measure** — the paired availability study + McNemar; false-open / flapping counts.
- **Defend** — `state_diagram.svg` + `DECISIONS.md` (D20-001…D20-006); every transition
  and provenance is traceable.
