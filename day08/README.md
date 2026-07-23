# FAULTLINE — Day 8: reproducible fault injection with independent ground truth

Inject component faults that are **reproducible** (deterministic *when* and
*what*) and carry **independent ground-truth labels** written at injection time —
so a later detector can be graded honestly, because the answer key was never
inside the sample it read.

> **Fail condition:** injected faults lack deterministic triggers or independent
> truth labels.
> **Status: not triggered** — every trigger is a pure function of
> `(spec, run_seed, seq, input_digest)` (byte-identical across repeats and, for
> the deterministic triggers, across seeds), and every label lives only in an
> out-of-band `GroundTruthLog`, never in the output or the trace span
> (0 label leaks across 5 seeds). See [CHECKPOINT-8.md](CHECKPOINT-8.md).

## The one idea

A fault worth measuring against is **data, not a patch**: declared in a uniform
spec, fired by a deterministic trigger, and labelled by a truth that is
*independent of its own observation*. Chaos engineering perturbs and watches;
FAULTLINE perturbs, **records what it did**, and keeps that record where the
system under test cannot read it. The label sits *beside* the sample (joined by
`span_id`), the way a supervised dataset keeps `y` out of `X`.

## What's here

```
faultline_inject/
  spec.py       the common 10-field FaultSpec (Build A) — exactly ten fields
  triggers.py   deterministic triggers: call_index / every_n / input_match /
                probabilistic (seeded, reproducible) — the WHEN, as a pure fn
  faults.py     severity -> deterministic effect per mode; InjectedFaultError
                — the WHAT / HOW MUCH (error/corrupt/truncate/drop/duplicate/stall)
  truth.py      GroundTruthLog + TruthEntry — labels written at injection time,
                out of band, one per call (a complete, contiguous labelling)
  boundary.py   InjectingChannel wraps any clean call boundary (Build B) +
                DemoChannel + a stable payload digest
  integrity.py  the attack + report: identical triggers across seeds, no leakage
scripts/
  make_evidence.py   regenerate the three evidence artifacts (deterministic)
tests/
  test_spec.py test_triggers.py test_boundary.py test_integrity.py  (45 tests)
evidence/
  injector_spec.json      the fault-spec set (the API's input contract)
  integrity_report.json   cross-seed attack: identical triggers + 0 leaks
  fault_trace.json        ONE reproducible fault trace with its ground truth
CHECKPOINT-8.md · LEARN-chaos.md · DECISIONS.md · REFLECTION.md
```

## Quickstart

```
python -m pytest tests/ -q     # 45 tests: spec, triggers, boundary, integrity
python scripts/make_evidence.py  # regenerate evidence (byte-reproducible)
```

Standard library only. Uses Day 4's tracer for the labelled trace; the label is
never written into a span.

## The 10-field fault specification (Build A)

| # | field | role |
|---|---|---|
| 1 | `fault_id` | stable identity, so a label joins back to a trace |
| 2 | `component` | which boundary to target (`"*"` = any) |
| 3 | `mode` | WHAT goes wrong (one of six modes) |
| 4 | `severity` | HOW MUCH — int 1..5, fixed magnitude schedule per mode |
| 5 | `trigger` | WHEN it fires (one of four triggers) |
| 6 | `trigger_value` | the trigger's parameter (string, for stable serialization) |
| 7 | `seed` | the fault's own seed; makes `probabilistic` reproducible |
| 8 | `rate` | target fire fraction for `probabilistic` (deterministic triggers must use 1.0) |
| 9 | `label` | the ground-truth class — independent truth, `fault:` prefixed |
| 10 | `spec_version` | schema version, so a meaning change shows in a diff |

Ten fields, machine-checked. If a fault can't be said in these ten, it's out of
scope — that constraint is the deliverable.

## How the boundary wrapper labels without leaking (Build B)

For each call, `InjectingChannel`:

1. digests the input and decides deterministically which spec (if any) fires;
2. writes the **ground truth first**, from that decision, into the out-of-band
   `GroundTruthLog` (`clean`, or the fault's label) — before any output exists;
3. produces the output: clean passthrough, a deterministic content mutation, a
   side-channel `cost` bump (`stall`, content unchanged), or a raised
   `InjectedFaultError` (`error`);
4. records a Day-4 span carrying **only** the public component/output — never
   the label.

Step 2 is written from the *decision*; step 4 from the *output*. That asymmetry
is why the truth is independent: a detector reading outputs and spans has no path
to the label. The `stall` mode is the clean proof — its output is byte-identical
to a clean call's, so no function of content can recover the label.

## Attack — identical triggers across seeds, no label leakage

`scripts/make_evidence.py` runs the spec set across five seeds
(`[20260718, 1, 42, 777, 100000]`) and proves, in `integrity_report.json`:

- **`all_seeds_reproducible: true`** — re-running a seed yields byte-identical
  outputs, truth, and cost (identical triggers).
- **`deterministic_triggers_seed_independent: true`** — `call_index`, `every_n`,
  `input_match` fire on the same calls regardless of seed.
- **`probabilistic_trigger_varies_across_seeds: true`** — the seeded trigger's
  pattern differs per seed yet is reproducible within each (variation without
  randomness).
- **`no_label_leakage: true`, `label_leaks_total: 0`** — no label or fault id
  appears in any output or span, across every seed.

## Mastery map

- **Explain** → [LEARN-chaos.md](LEARN-chaos.md) (fault injection vs random chaos)
- **Build** → `faultline_inject/` (the spec, triggers, wrapper, truth log)
- **Debug** → `evidence/fault_trace.json` (one labelled trace, join by `span_id`)
- **Measure** → `evidence/integrity_report.json` (reproducibility + leakage counts)
- **Defend** → [DECISIONS.md](DECISIONS.md), [CHECKPOINT-8.md](CHECKPOINT-8.md)
