# FAULTLINE Evaluation Dataset — `de5068d574cae9fd`

A versioned, leakage-resistant, oracle-grounded evaluation dataset over the six-fault spectrum (F1-F6).

## Version & provenance

- **dataset_version:** `de5068d574cae9fd` (content hash of this manifest)
- **generator_version:** `dataset-1.0.0`
- **samples:** 44  (train 27 / test 17)
- **split method:** stratified by (modality, is_fault); within each stratum, samples sorted by sample_id, the first 2/5 (>=1, <n) assigned to test. Deterministic and balanced across families.

## Composition (samples per modality)

| Modality | fault | clean |
|---|---|---|
| F1 | 6 | 3 |
| F2 | 6 | 3 |
| F3 | 4 | 3 |
| F4 | 2 | 3 |
| F5 | 4 | 3 |
| F6 | 4 | 3 |

## Fields (per sample)

`sample_id` (content hash of config) · `modality` (F1-F6) · `is_fault` · `kind` · `severity` (tier) · `seed` · `expected_label` (oracle-grounded) · `expected_faulty` · `split`.

## Leakage controls

- sample_id = content hash of config (identity unambiguous)
- split is a deterministic, stratified, disjoint partition
- expected_label grounded in injection truth, never a detector
- dataset_version = content hash of this manifest (stale reuse detectable)

## Intended use

Measure detection accuracy of the F1-F6 detectors against injection truth on the held-out **test** split. Labels are grounded in the injection oracle, not in any detector. Results are bound to this `dataset_version`; a result computed against a different version is rejected as stale.

## Reproducible eval command

```
python day13/scripts/eval.py --split test
```

Deterministic: no wall clock, no RNG outside seeded fault injection.

