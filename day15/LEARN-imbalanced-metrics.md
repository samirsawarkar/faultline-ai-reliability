# LEARN — imbalanced metrics, and why aggregates lie

Q2 is a measurement mission, so the lesson is about *how detection accuracy is
reported* — specifically, how a single number hides exactly the failures you most
need to see, and what to report instead.

## The aggregate is the enemy of honesty

Suppose someone says "the detector suite is 62% accurate." That number is true and
useless. Pool six fault families and you learn nothing about any of them: F4 and F6
are caught every time (recall 1.0), F2 is caught a third of the time (0.33), and the
average describes none of the six. Worse, the *composition* of the sample drives the
number — add more F4 samples and "accuracy" rises without any detector improving.
A pooled metric confounds detector quality with dataset mix.

The discipline Q2 enforces: **report per class, always, and treat the aggregate as
a diagnostic, not a headline.** The per-class confusion matrix is the ground truth;
the aggregate is only useful as a *warning sign*.

## Micro vs macro — read the gap

Two ways to average across classes, and the gap between them is informative:

- **Micro** pools every sample and computes one rate. It is dominated by the classes
  with the most samples, and it is what a naive "overall accuracy" reports.
- **Macro** computes each class's rate and averages the rates, giving every class
  equal weight regardless of size.

When micro ≈ macro, the classes are balanced and behave similarly. When they
**diverge** (here micro 0.615, macro 0.667), the classes are imbalanced in accuracy
— some are much easier than others — and *that divergence is the tell that a single
number is hiding a spread.* Neither is "right"; the point is to report both and let
the gap flag the imbalance.

## Precision, recall, and which error you are hiding

An aggregate accuracy blends two very different errors:

- **False positives** (flagging a clean sample) cost trust and trigger needless
  recovery. Precision = TP / (TP + FP) isolates them.
- **False negatives** (missing a real fault) are the dangerous ones in reliability —
  a fault that slips through undetected. Recall = TP / (TP + FN) isolates them.

Accuracy can look great while recall is terrible if faults are rare (the classic
class-imbalance trap: "99% accurate" on data that is 99% clean means the detector
may catch nothing). FAULTLINE reports precision and recall separately, per class,
so neither error can hide inside the other. In Q2 the split is stark: **precision is
1.0 everywhere (no false positives), and all the error is false negatives** — which
is exactly where a pooled accuracy would have buried the story.

## Not all misses are equal

The last move is to classify the false negatives, because "10 misses" hides an
actionable distinction:

- **Threshold-reducible** misses (low-severity F1/F2) are below a detector's budget
  or range. They are a *policy choice*: tighten the schema range or the latency
  budget and they are caught — at some cost in false positives. They are on a dial.
- **Irreducible semantic escapes** (F3 `drift_value`, F5 `context_drift`) are
  structurally identical to correct outputs. No threshold catches them, because
  there is nothing structural to key on. They require a different tool entirely — an
  oracle or a validated judge (Mission 16).

Reporting the taxonomy turns a flat error count into a roadmap: tune the thresholds
for the reducible misses, and build semantic evaluation for the irreducible ones.

## The through-line for FAULTLINE

Q2 is where Day 11's split hypothesis meets Day 13's dataset and Day 14's intervals.
The answer: detection accuracy is bimodal and must be read per class; the deterministic
faults are caught (modulo a threshold dial) with no false positives, and the semantic
faults leave an irreducible false-negative set. The intervals are wide at this sample
size, so the *group* comparison is directional — but the escapes are undetectable by
construction, which is the part that does not depend on n.

## References worth reading next

- Class imbalance and the accuracy paradox; precision/recall and PR curves
  (Davis & Goadrich, 2006).
- Macro vs micro averaging in multi-class evaluation (any IR/classification text;
  Manning, Raghavan & Schütze, *Introduction to Information Retrieval*).
- Confusion-matrix-first reporting and per-class error analysis (Ng's error-analysis
  guidance in *Machine Learning Yearning*).
