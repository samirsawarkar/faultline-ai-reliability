# LEARN — judge reliability and inter-rater agreement

Day 16 introduces the first component of the project that *is* a model — an LLM
judge — and the lesson is about the discipline that keeps a model's opinion from
quietly becoming ground truth. Three ideas: agreement done honestly, the failure
modes LLM judges actually have, and where a judge is allowed to live.

## Agreement, done honestly: raw vs kappa, and the human ceiling

The naive way to validate a judge is "how often does it agree with a human?" — raw
agreement. It flatters. If humans accept 80% of candidates and the judge accepts 80%
too, they will agree ~68% of the time *by chance alone*, before the judge understands
anything. **Cohen's kappa** corrects for that: it subtracts the agreement expected
from the marginals, so κ = 0 means "no better than chance" and κ = 1 means perfect.
Day 16's judge shows raw agreement 0.75 but κ 0.50 — the gap is the chance agreement
the raw number was hiding.

The second honesty move is the **human ceiling**. Humans do not agree with each other
perfectly; on this set two human raters reach κ 0.80, not 1.0. Judging the LLM against
a perfect 1.0 would be unfair and would guarantee it "fails." The right bar is the
inter-rater ceiling: a judge that reaches human-vs-human agreement is as reliable as
a human on this task. Ours (κ 0.50) sits below the ceiling (κ 0.80), so it is *not* a
human substitute — a fact you only see because both numbers are reported.

## The failure modes LLM judges actually have

LLM-as-judge is a real technique (and a large literature), but it comes with
well-documented biases that a validation harness must probe for, not assume away:

- **Positional bias.** In pairwise comparisons, judges tend to prefer whichever
  candidate is presented first (or last), independent of quality. Day 16 exposes this
  by presenting every pair in *both* orders: an order-dependent winner is bias. Our
  judge is 100% order-dependent on close calls — so the mitigation (prefer pointwise
  scoring, or average both orders) is not optional.
- **Verbosity / self-preference / leniency.** Judges often reward longer answers,
  prefer outputs that look like their own, and drift lenient. Our judge is measurably
  lenient (it over-accepts: 6 false accepts, 0 false rejects) and has a **failure
  slice** — it tolerates token-order drift humans reject. Reporting per-slice, not
  just an aggregate, is what makes that slice visible.
- **Miscalibration.** A judge's confidence rarely matches its accuracy; treat its
  verdict as a noisy label, never a probability, until calibrated.

The point of the harness is not to prove the judge is good — it is to find, name, and
quantify exactly where it is bad, so the judge can be used only where it is trustworthy.

## Where a judge is allowed to live

The load-bearing decision is scope. FAULTLINE keeps a hard line: **core success is
decided by the oracle (Day 1), never by the judge.** A model's opinion, however well
validated, cannot become the definition of "the system worked" — that would
re-introduce the eyeballing the whole project set out to replace, now dressed up as a
number. The judge is confined to the one question deterministic detection cannot
answer (fallback quality for the F3/F5 escapes), used only outside its failure slice,
with its positional bias mitigated, and never as the arbiter of success. That is why
the judge card's first prohibition is a prohibition, not a caveat.

The general rule: **validate before you trust, measure against the human ceiling not
perfection, probe for the known biases, and give the judge the narrowest possible
job.** A judge earns scope by passing the harness; it does not get scope by default.

## References worth reading next

- Cohen (1960), *A coefficient of agreement for nominal scales*; Landis & Koch (1977)
  for the κ interpretation bands.
- Zheng et al. (2023), *Judging LLM-as-a-Judge* (MT-Bench / Chatbot Arena) — positional,
  verbosity, and self-enhancement biases and mitigations.
- Inter-annotator agreement in NLP (Artstein & Poesio, 2008) — why the human ceiling,
  not 1.0, is the bar.
