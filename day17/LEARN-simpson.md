# LEARN — aggregation traps and Simpson's paradox

Day 17 is about the ways a single number lies. The deepest of them is Simpson's
paradox: an aggregate can point the *opposite* way from every subgroup it
summarises. Understanding why — and building the discipline to catch it — is the
lesson.

## Simpson's paradox, concretely

The classic example is the 1970s kidney-stone study. Treatment A beats treatment B
on small stones, and A beats B on large stones — yet B beats A *overall*. How? A
was given mostly to the hard (large-stone) cases and B to the easy ones, so B's
overall number is inflated by an easy case mix. The aggregate confounds "which
treatment is better" with "which treatment got the easy cases."

FAULTLINE has its own instance. Aggregated, the deterministic detector group beats
the semantic group (0.81 vs 0.74). But **at severity 3 it reverses**: the
deterministic group scores 0.0 and the semantic group 0.67. The cause is identical
to the kidney stones — the severity *mix* differs between the groups. At severity 3
the deterministic group is represented only by F2 latency faults, which sit below
the detector's budget and are all missed; the semantic group at that severity
includes cases its invariant catches. Slice by the confounder and the headline
ordering flips.

The moral: **an aggregate is a weighted average, and the weights can carry the
story.** Whenever you compare two groups whose subgroup composition differs, the
aggregate comparison is suspect until you check the slices.

## The two traps that make subgroup analysis itself dangerous

Slicing is the cure, but done carelessly it becomes two new diseases:

1. **The small-n trap.** Slice finely enough and every cell is tiny. A 2-sample
   subgroup at 0% "accuracy" looks alarming but carries almost no information — its
   Wilson interval is enormous. FAULTLINE gates any subgroup below a minimum sample
   size as *insufficient*: reported, but never a conclusion. Most fault×severity
   cells here are n=2, so most fine-grained "findings" are correctly withheld.
2. **The multiple-comparisons trap.** Test twenty subgroups at α=0.05 and you
   *expect* one false "significant" result by chance. This is how p-hacking and
   "we found a subgroup where X works!" happen. Holm-Bonferroni corrects for the
   size of the family so a claim has to clear a stricter bar. Here, several
   subgroup intervals exclude the headline, but **after correction none is
   individually significant** — the honest reading is "a real-looking spread that
   the data cannot yet certify."

Holding both disciplines at once is uncomfortable: the small-n gate and the
multiple-comparison correction will often tell you that your exciting subgroup
finding is not yet real. That discomfort is the point — it is what separates a
finding from an artifact.

## Why the gate, not just a report

The mission's fail condition is not "fail to compute subgroups" — it is "a subgroup
contradicts the headline and is *ignored*." So the deliverable is not only the
sliced numbers; it is a **gate** that recomputes the contradiction set
independently and refuses to pass if any is dropped. This encodes a cultural rule
as code: you do not get to publish the flattering aggregate and bury the slice that
disagrees. Every reversal and every interval that excludes the headline is carried
into the report, classified by significance and power, and the audit fails the
moment one goes missing.

## The through-line for FAULTLINE

Day 15 said "report per class, not just an aggregate." Day 17 hardens that into a
search-and-gate: actively look for reversals, apply min-sample and
multiple-comparison discipline so the search is honest, and make ignoring a
contradiction impossible to do silently. The result here is deliberately modest —
a real severity-3 reversal and a systematic low-severity miss, none significant at
n=44 — and saying exactly that, with its limitations on top, is the mastery.

## References worth reading next

- Simpson (1951); Blyth (1972) on the paradox; the Bickel et al. (1975) Berkeley
  admissions case; the Charig et al. (1986) kidney-stone example used here.
- Holm (1979), *A simple sequentially rejective multiple test procedure*; Benjamini
  & Hochberg (1995) for the FDR alternative.
- Gelman & Loken, *The Garden of Forking Paths* (2013) — why uncorrected subgroup
  search invents findings.
