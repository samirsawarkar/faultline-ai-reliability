# REFLECTION.md — five-minute mission reflection (Day 13)

**Mission.** Create a leakage-resistant, versioned evaluation system grounded in
the oracle.
**Fail condition.** Dataset versions, splits, or leakage controls are ambiguous. —
*Not triggered:* the version is a content hash, the split is a deterministic
stratified disjoint partition, and every leakage control is enforced and audited
(contamination caught, stale reuse blocked, no label leakage). See [CHECKPOINT-13.md](CHECKPOINT-13.md).

**Do we need an LLM API now? No.** This is evaluation *infrastructure*: versioning,
splits, immutable results, and leakage controls. The labels are grounded in the
Day-8 injection oracle, which is deterministic. When a real subject arrives, it is
just another modality behind `run_and_predict`; the harness measures it unchanged.

**The sharpest decision.** Content-addressing the dataset version (D13-001) and
binding results to it (D13-004). Together they make stale reuse a *detected* event
rather than a silent one — the single most common way eval numbers go wrong is
being quoted after the data moved. A hash comparison closes that hole for free.

**The subtle one.** Stratifying the split by (modality, kind), not just
(modality, is_fault). The first version left kind coverage to luck and the F3
`drift_value` escape landed only in train — so the held-out set never exercised the
hard case. Stratifying by kind guarantees the semantic escapes appear in test,
which is why the test-split recall (0.727) honestly reflects the Q2 split instead of
flattering it.

**Mastery gate.**
- *Explain* — [LEARN-eval-infra.md](LEARN-eval-infra.md): trust is in the plumbing.
- *Build* — dataset + versioning + splits + immutable runner + leakage controls.
- *Debug* — [`evidence/splits.json`](evidence/splits.json) + `eval_result.json`.
- *Measure* — [`evidence/eval_result.json`](evidence/eval_result.json), bound to a
  `dataset_version`.
- *Defend* — [DECISIONS.md](DECISIONS.md), D13-001…D13-007.

**What I'd watch next.** Mission 14 adds intervals + paired statistical design on
top of this dataset (Wilson CIs, paired comparisons); Mission 15 (Q2) reports
detection accuracy per family with those intervals on the held-out split; and the
versioned dataset becomes the fixed ruler every later measurement is quoted against.
