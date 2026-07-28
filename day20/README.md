# FAULTLINE — Day 20: M3/M4 — circuit breaker + provider fallback

Restore availability when a provider fails, **without hiding the failure** (degraded
answers are flagged) and **without blocking healthy traffic** (a tuned breaker rides
out isolated blips). Every breaker transition and every fallback provenance is
recorded, so recovery is fully traceable.

> **Fail condition:** breaker transitions or fallback provenance cannot be traced.
> **Status: not triggered** — the breaker appends every `{from, to, reason, tick}`
> transition to a log, and every request carries `served_by` / `is_fallback` /
> `is_degraded` provenance mirrored into a Day-4 trace. See [CHECKPOINT-20.md](CHECKPOINT-20.md).

## The one idea

Day 19 proved that under a correlated outage, retries are pure amplification — you
need a breaker. A breaker stops calling a failing dependency (protecting it from a
retry storm), but a breaker *alone* trades a little availability for that protection.
So it is paired with a **fallback chain** (primary → secondary → degraded) that
restores availability, and a **degraded tier** that keeps requests answered while
honestly flagging them as second-best. The whole thing is only trustworthy if you can
trace *why* each request was served the way it was — hence provenance everywhere.

## What's here

```
faultline_breaker/
  breaker.py    CircuitBreaker: CLOSED/OPEN/HALF_OPEN, rolling-window threshold,
                cooldown, half-open trials, and a recorded transition log
  fallback.py   route_fallback: primary -> secondary -> degraded, each with provenance
  runner.py     run_stream: request stream through breaker+fallback, provenance +
                Day-4 trace + transition log (breaker=None = the no-breaker baseline)
  experiment.py false_open, flapping, fallback_failure + a 3-way paired outage study
  diagram.py    the SVG state-transition diagram + a transition timeline renderer
scripts/ make_evidence.py
tests/   test_breaker.py  (9 tests)
evidence/ breaker_report.json  state_diagram.svg  transitions_trace.json
CHECKPOINT-20.md · LEARN-breaker-degradation.md · DECISIONS.md · REFLECTION.md
```

## Quickstart

```
python -m pytest tests/ -q       # 9 tests
python scripts/make_evidence.py  # regenerate the report, SVG diagram, traced run
```

Standard library only. Builds on Day 4 (traces), Day 14 (McNemar), Day 19 (why).
Virtual-tick clock, so every run is byte-reproducible.

## The results (canonical outage: primary down for ticks [20, 40))

**A full traced transition cycle** — including a failed half-open trial mid-outage:

```
[t22] closed→open (failure_threshold) → [t32] open→half_open (cooldown_elapsed)
→ [t32] half_open→open (half_open_failed) → [t42] open→half_open (cooldown_elapsed)
→ [t43] half_open→closed (recovered)
```

**Paired study** (naive / breaker-only / breaker+fallback):

| config | availability | primary calls | healthy blocked |
|---|---|---|---|
| naive (no breaker, no fallback) | 0.667 | 60 | 0 |
| breaker only | 0.633 | **42** | 2 |
| breaker + fallback | **1.00** | 42 | 2 |

- The **breaker cuts 18 calls** to the failing primary (storm protection) — but on its
  own it *dips* availability (it refuses some calls), which is the honest cost.
- The **fallback restores availability to 1.0** (+0.333); McNemar naive-vs-breaker+fb
  on "answered" is **p ≈ 2e-6, significant**.

**Attacks:**

- **False opens:** a twitchy breaker (open on 1 failure) blocks **25 healthy** calls on
  isolated blips; a tuned breaker (3-of-5 window) blocks **0**. Tuning is the whole game.
- **Flapping:** a marginal dependency drives a too-eager breaker through **21**
  transitions; a longer cooldown + higher success-threshold damps it to **7**.
- **Fallback failure:** primary *and* secondary both down → the degraded tier keeps
  availability at **1.0** with **0 unanswered**, every answer flagged degraded (nothing hidden).

## Mastery map

- **Explain** → [LEARN-breaker-degradation.md](LEARN-breaker-degradation.md)
- **Build** → `faultline_breaker/` (breaker, fallback, runner)
- **Debug** → `evidence/transitions_trace.json` (timeline + per-request provenance + trace)
- **Measure** → the paired availability study + McNemar
- **Defend** → `evidence/state_diagram.svg`, [DECISIONS.md](DECISIONS.md), [CHECKPOINT-20.md](CHECKPOINT-20.md)
