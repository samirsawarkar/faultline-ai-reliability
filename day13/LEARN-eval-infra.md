# LEARN — evaluation infrastructure, and the process behind it

Day 13 builds an evaluation harness, so the thing to learn is not a metric but a
*process*: how mature evaluation systems keep results trustworthy over time. The
best references are the public eval frameworks and the dataset-documentation
literature; below is what each contributes and the implementation decision it drove
here.

## What the field already settled

**Held-out test splits and contamination control.** Every serious ML evaluation
separates train/dev/test, and the modern failure mode is *contamination* — test
data leaking into training (or into a model's pretraining corpus). Benchmarks like
the ones aggregated by HELM (Stanford) and the EleutherAI `lm-evaluation-harness`
treat contamination as a first-class threat, not an afterthought. *Decision here:*
a deterministic, disjoint split, plus an explicit contamination check and an attack
that tries to violate it (D13-002, D13-006).

**Dataset versioning and content addressing.** Reproducible pipelines (DVC,
`datasets` fingerprints, content-addressed stores) version data by *content*, not
by a hand-maintained number, so "same data" is a hash comparison and drift is
impossible to miss. *Decision here:* `dataset_version` = hash of the whole manifest
(D13-001), and results bound to it so stale reuse is detectable (D13-004).

**Dataset documentation.** *Datasheets for Datasets* (Gebru et al., 2021) and
*Model Cards* (Mitchell et al., 2019) established that a dataset should ship a card
describing its composition, provenance, intended use, and limitations. *Decision
here:* `DATASET_CARD.md` records composition per modality, the split method, the
leakage controls, and the reproducible command.

**Immutable, provenance-carrying results.** Experiment trackers (MLflow, Weights &
Biases) record the exact code + data + config behind every number, because a metric
without provenance is unciteable. *Decision here:* a frozen `EvalResult` carrying
`dataset_version`, `code_version`, and a derived `result_id` (D13-004).

**Labels independent of the system under test.** The whole point of an oracle or a
held-out gold label is that it is not produced by the model being graded. *Decision
here:* labels grounded in the injection oracle, and a detector that structurally
cannot receive the label (D13-003, D13-005).

## Turning process into implementation

The recurring lesson across all of these is that **trust in an evaluation is a
property of its plumbing, not its arithmetic.** Precision and recall are trivial to
compute; what makes them defensible is that (a) the labels are independent, (b) the
test set is genuinely held out and uncontaminated, (c) the data is versioned so a
number can be traced to exactly the bytes it came from, and (d) a result cannot
outlive the data it describes. Day 13 encodes each of those as a mechanism a
reviewer can re-run, and demonstrates the two most common ways the plumbing leaks —
train/test contamination and stale-result reuse — being caught.

## The FAULTLINE-specific twist

One thing generic eval infrastructure does not have to worry about, but FAULTLINE
does: the *labels themselves come from an oracle over injected faults*, so the
dataset is only as honest as the injection truth from Day 8. Because that truth is
written out-of-band at injection time and never leaks into the observable features
(Day 8), the label independence this day relies on is inherited, not re-earned. The
evaluation harness is the last link in a chain — inject truthfully (Day 8), detect
without peeking (Days 9-11), catalogue faithfully (Day 12), evaluate without
contamination (Day 13) — and each link is only trustworthy because the ones before
it are.

## References worth reading next

- HELM: Liang et al., *Holistic Evaluation of Language Models* (2022).
- EleutherAI `lm-evaluation-harness` (design docs on task/version pinning).
- Datasheets for Datasets (Gebru et al., 2021); Model Cards (Mitchell et al., 2019).
- Data versioning: DVC docs; HuggingFace `datasets` fingerprinting.
- Contamination: Sainz et al., *Data Contamination* surveys; the "train-test
  overlap" literature.
