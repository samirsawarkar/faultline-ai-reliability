# FAULTLINE — Day 6: exact replay, and an honest boundary

Capture a run into a **replay bundle**, replay it **byte-for-byte**, and document
precisely what a real provider **cannot** reproduce.

> **Fail condition:** replay claims exceed what captured state can reproduce.
> **Status: not triggered** — playback and re-execution are reported as separate
> claims, and `evidence/replay_report.json` (`claims_hold: true`) plus
> [LIMITATIONS.md](LIMITATIONS.md) enumerate the boundary.

## What's here

```
faultline_replay/
  bundle.py     replay-bundle format: seeds/inputs/recorded calls/state/versions
                + canonical bytes, digest, and a version/schema guard
  providers.py  SimulatorProvider (pure) vs FlakyProvider (uncaptured entropy);
                LiveChannel (record) vs ReplayChannel (playback, diverge loudly)
  program.py    the agent/model/tool program (built on Day-4 Tracer)
  capture.py    capture_run: live run -> bundle (Build A)
  replay.py     replay_bundle: deterministic replay harness (Build B)
  diff.py       structured diff between traces/bundles
  report.py     the replay-difference report (playback vs re-execution)
scripts/
  make_evidence.py  regenerate bundles + replay report
  replay_demo.py    capture, replay, show the diff (and the flaky boundary)
tests/
  test_replay_exact.py  simulator replays AND re-executes byte-identically
  test_boundary.py      flaky: replays exact, re-executes divergent; claims bounded
  test_bundle.py        version guard + replay-divergence detection
evidence/
  bundle_simulator.json   the replay bundle (deterministic)
  replay_simulator.json   the replay output (matches captured trace)
  replay_report.json      simulator vs real-provider reproducibility
  environment.json        captured runtime (informational, not diff-gated)
LIMITATIONS.md · LEARN-reproducibility.md · DECISIONS.md · REFLECTION.md
```

## Quickstart

```
python -m pytest tests/ -q          # 11 tests: exact replay + boundary + guards
python scripts/replay_demo.py                  # simulator: diff_count = 0
python scripts/replay_demo.py --provider flaky # replay exact; re-exec diverges
python scripts/make_evidence.py                # regenerate evidence
```

Standard library only; traces built on Day 4. No LLM — see REFLECTION.md.

## The boundary in one table

| | replay (playback) | re-execution (recompute) |
|---|---|---|
| **simulator** | ✅ exact | ✅ exact (pure function of captured state) |
| **real provider** (stand-in) | ✅ exact | ❌ diverges (uncaptured entropy) |

Replaying serves the bytes we recorded, so it is exact for anything. Only the
deterministic simulator *also* re-executes identically. We never claim to
regenerate a real provider — that's the whole point.

## Mastery map

- **Explain** → `LEARN-reproducibility.md`
- **Build** → `faultline_replay/`
- **Debug** → `ReplayDivergence` / `VersionMismatch` fail loudly, never silently
- **Measure** → `replay_report.json`
- **Defend** → `DECISIONS.md`, `LIMITATIONS.md`
