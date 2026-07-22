# DECISIONS.md — Day 13 (evaluation harness + versioned dataset) decision log

Append-only. Date · id · decision · why · reversal cost.

---

### 2026-07-23 · D13-001 · Content-addressed dataset version
**Decision.** `dataset_version` = sha256 of the full manifest (generator version +
every sample descriptor), truncated. Any change to a seed, tier, config, or label
changes the version.
**Why.** "Dataset versions must not be ambiguous." A content hash is the least
ambiguous version possible: two datasets are the same iff their version matches,
and a stale result is detectable by a version mismatch. No manual version bumps to
forget.
**Reversal cost.** None; it is derived, not maintained.

### 2026-07-23 · D13-002 · Deterministic, stratified, disjoint splits
**Decision.** The split is a pure function of the sample set: stratify by
(modality, kind), sort each stratum by sample_id, assign the first ≈40% to test.
**Why.** Splits must be unambiguous and reproducible (no RNG, no wall clock), and
they must be *useful*: stratifying by kind guarantees every fault kind — including
the semantic escapes — appears in both train and test, so the test split actually
exercises the hard cases. Disjointness is by construction.
**Reversal cost.** Low; the stratum key or fraction is a one-line change (and would
change the version, as it should).

### 2026-07-23 · D13-003 · Labels grounded in the injection oracle, never a detector
**Decision.** `expected_label` / `expected_faulty` come from the sample's injection
config (fault family or clean); the detector never contributes to a label.
**Why.** An evaluation is only honest if the answer key is independent of the thing
being graded (Days 8-12's discipline). Grounding labels in the oracle is what makes
recall/precision on this dataset a real measurement.
**Reversal cost.** None; it is the definition of the label.

### 2026-07-23 · D13-004 · Results are immutable and bound to data + code versions
**Decision.** `EvalResult` is a frozen dataclass carrying `dataset_version`,
`code_version`, `split`, and a `result_id` hashed from them. `validate_result`
returns fresh/stale against a dataset.
**Why.** A result detached from its inputs is a landmine — it gets quoted after the
data or code moved on. Binding the versions into the result (and refusing to call a
mismatched result fresh) turns stale reuse from a silent bug into a detected one.
**Reversal cost.** None; additive metadata.

### 2026-07-23 · D13-005 · The detector receives only injection config (label non-leakage)
**Decision.** `run_and_predict` takes (modality, is_fault, kind, severity, seed) —
never the expected label — so a prediction is structurally independent of the
answer key.
**Why.** The subtlest leakage is a detector that can peek at the label. Making the
label impossible to pass to the detector removes the failure mode by construction,
not by discipline.
**Reversal cost.** None; it is an API shape.

### 2026-07-23 · D13-006 · Ship the attacks as committed evidence, not just checks
**Decision.** `attempt_train_test_contamination` and `attempt_stale_reuse` actively
try to break the guards, and their outcomes go in `leakage_report.json`.
**Why.** A "leakage-resistant" claim is only credible if the resistance is
demonstrated against an attempt, not merely asserted. Committing the attack results
lets anyone see the guard win.
**Reversal cost.** None; additive.

### 2026-07-23 · D13-007 · Reuse Days 9-11 runners/detectors; the harness adds only versioning + splits
**Decision.** `predict.run_and_predict` dispatches to the owning day's runner and
detector; Day 13 contributes the dataset, splits, versioning, immutability, and
leakage controls — not new detection logic.
**Why.** The evaluation must measure the *same* detectors the catalog ships, or the
numbers mean nothing. Reuse keeps the eval faithful and the new code focused on the
evaluation infrastructure the mission asks for.
**Reversal cost.** Low; a new modality is a new dispatch branch + config entry.
