# FAULTLINE — Day 17: subgroup analysis + measurement gate

Find where the aggregate metric hides failure. Slice the evaluation by **fault,
severity, hop count and outcome**; apply **minimum-sample** and
**multiple-comparison** discipline; hunt for **reversals** (Simpson's paradox); and
**gate** the headline so no contradicting subgroup can be ignored.

> **Fail condition:** a subgroup contradicts the headline claim and is ignored.
> **Status: not triggered** — every subgroup whose interval excludes the headline,
> and every ordering reversal, is surfaced and acknowledged; the evaluation audit
> independently recomputes the contradiction set and fails if any is dropped. See
> [CHECKPOINT-17.md](CHECKPOINT-17.md).

## The one idea

An aggregate is a weighted average, and a weighted average can point the opposite
way from every subgroup it summarises (Simpson's paradox). Day 15 already reported
per class; Day 17 goes further: it *searches* for reversals and unstable
conclusions across every slice, applies the discipline that stops noise from
looking like a finding, and makes ignoring a contradiction a gate failure.

## What's here

```
faultline_subgroups/
  gate.py       min-sample gate, Wilson CI, one-proportion z-test, Holm-Bonferroni
  subgroups.py  slice_by(dims): a gated rate per subgroup
  reversal.py   Simpson's-paradox / ordering-reversal detector (+ known-case verify)
  analysis.py   apply to Day-15 detection outcomes + Day-7 hop curve
  report.py     assemble the report + the measurement gate
  audit.py      independently re-derive contradictions; fail if any is ignored
  tables.py     render SUBGROUP_FINDINGS.md (limitations first)
scripts/ make_evidence.py
tests/   test_subgroups.py test_reversal_audit.py  (11 tests)
evidence/ subgroup_report.json evaluation_audit.json SUBGROUP_FINDINGS.md
CHECKPOINT-17.md · LEARN-simpson.md · DECISIONS.md · REFLECTION.md
```

## Quickstart

```
python -m pytest tests/ -q       # 11 tests
python scripts/make_evidence.py  # regenerate the subgroup report + audit (byte-reproducible)
```

Standard library only. Reads Day 15 (detection outcomes), Day 14 (Wilson/normal),
and Day 7 (committed hop curve).

## The findings (dataset `de5068d574cae9fd`, n=44)

- **Headline:** overall detection accuracy **0.773**.
- **A real ordering reversal.** Aggregated, the deterministic group beats the
  semantic group (0.81 vs 0.74). But **at severity 3 it reverses**: deterministic
  **0.0** (n=2, only F2 latency, below its budget) vs semantic **0.667** (n=6). The
  severity mix differs between the groups — a textbook confound — so the headline
  ordering does not hold in that slice. Surfaced, not hidden.
- **Low-severity faults are systematically missed** (severity-1 F1/F2 → 0.0; the
  clean subgroup → 1.0): both intervals exclude the headline.
- **Hop count:** Day 7's "naive p^n overpredicts" headline **fails at hops 1–2**
  (naive lies inside the measured CI there); it first holds at hop 3.
- **Discipline matters:** after Holm correction across the reportable subgroups,
  **none** of these contradictions is individually significant at this n — the
  spread is real but under-powered. That honesty *is* the finding.

## The measurement gate (the fail condition, refused)

`evaluation_audit.json`: the audit recomputes the contradiction set from the
analysis and asserts the report acknowledged **every** one; the reversal detector
is verified against a known Simpson's paradox; min-sample and Holm discipline are
confirmed. `test_audit_fails_if_a_contradiction_is_ignored` drops one and shows the
gate flip to failed — so a hidden subgroup cannot pass silently.

## Mastery map

- **Explain** → [LEARN-simpson.md](LEARN-simpson.md)
- **Build** → `faultline_subgroups/` (slicer, gate, reversal detector, audit)
- **Debug** → `evidence/subgroup_report.json` (per-slice CIs, the reversal table)
- **Measure** → gated rates + Holm-corrected tests; the severity-3 reversal
- **Defend** → `evidence/evaluation_audit.json`, [DECISIONS.md](DECISIONS.md),
  [CHECKPOINT-17.md](CHECKPOINT-17.md)
