# FAULTLINE — Day 1

Lock the thesis and build the seeded environment whose oracle makes every later
number honest.

> **Mastery gate:** you must be able to *explain*, *build*, *debug*, *measure*,
> and *defend* this. See the map at the bottom.

## What's here

```
faultline/
  env.py       deterministic environment generator (corpus + questions + answers)
  oracle.py    oracle_check: correctness AND required-source verdict
scripts/
  gen.py                    emit a canonical env, or per-seed digests
  handcheck.py              10 hand-checked oracle cases (enforced)
  experiment_determinism.py 20 seeds × 2 processes → determinism_report.txt
tests/
  test_determinism.py       the pass/fail gate for Day 1
  test_oracle.py            oracle behavior + one-source-per-answer guarantee
evidence/
  seed_digests.tsv          sha256 per seed, 0..19
  determinism_report.txt    byte-identical proof across processes/hashseeds
  oracle_handcheck.json     the 10 cases and verdicts
  env_seed7.json            a full sample environment
MEASUREMENT.md  the contract every number obeys
DECISIONS.md    the decision log (D-001 … D-007)
THESIS.md       the one-paragraph FAULTLINE thesis
LEARN.md        deterministic seeding + why an oracle beats eyeballing
```

## Quickstart

```
python -m pytest tests/ -v                 # 11 tests: determinism + oracle gate
python scripts/experiment_determinism.py   # regenerate the determinism report
python scripts/handcheck.py                # human-readable oracle hand-check
python scripts/gen.py --seed 7             # print a canonical environment
python scripts/gen.py --digests 0 19       # per-seed sha256
```

Requires only the Python standard library (developed on CPython 3.9).

## Mission status

- [x] Deterministic env generator — `faultline/env.py`
- [x] `oracle_check` — `faultline/oracle.py`
- [x] `MEASUREMENT.md`
- [x] Determinism test — `tests/test_determinism.py` (incl. cross-process /
      cross-hashseed attack)
- [x] 20 seeds generated twice, byte-identical — `evidence/determinism_report.txt`
- [x] 10 oracle cases hand-checked — `evidence/oracle_handcheck.json`

**Fail condition (env or oracle not deterministic): not triggered** — proven by
the test suite and the committed digests.

## Mastery map

- **Explain** → `THESIS.md`, `LEARN.md`
- **Build** → `faultline/`, `scripts/`
- **Debug** → `LEARN.md` §1 (the four determinism leaks and how each is closed)
- **Measure** → `MEASUREMENT.md`, `evidence/`
- **Defend** → `DECISIONS.md` (every choice, its why, and its reversal cost)
