# Day 28 standalone figure captions

Each caption states the population, comparison, principal result, and the limitation needed to read the figure without the article.

## Figure 1

Figure 1. Required tool depth exposes a non-constant reliability process. Across 500 seeded trials at each depth, the measured curve first excludes naive p₁ⁿ at hop 3 (0.818, 95% CI 0.781797–0.849354, versus 0.91833); at hop 8 it is 0.288 versus 0.796765. The result is specific to the configured decay simulator, and intervals widen at deep hops as fewer runs reach later steps.

## Figure 2

Figure 2. On the 44-example labelled set, detector precision was 1.0 but micro recall was 0.615385. The six family intervals are wide and overlapping; the informative evidence is the miss audit: all 10 false negatives were surfaced, with 6 threshold-reducible cases and 4 irreducible semantic escapes. The plot is descriptive and does not establish that one fault group is superior.

## Figure 3

Figure 3. Each retry scenario used 200 shared seeds. Under independent faults, K=3 achieved 0.76 success at 1.9× attempt amplification and p99 latency 76.0; under correlated faults, the last acceptable point was K=2, with 0.365 success at 1.735× and p99 53.4. These recommendations enforce the configured 2.0× amplification and 120-unit p99 ceilings; they are not universal retry constants.

## Figure 4

Figure 4. Across 120 paired requests with 40 scheduled primary outages, fallback raised availability from 0.6667 to 1.0 while strict quality among answered requests fell from 1.0 to 0.75. Of the 40 fallback answers, 30 were silently degraded. The advisory detector recalled 0.6667 of degraded fallback answers and missed all 10 borderline-token cases, so it was not used for core success scoring.

## Figure 5

Figure 5. Over 400 shared seeds, P4 selective guarded was the base-envelope winner: correct success 0.9325 (95% CI 0.9036–0.9532), mean cost 1.4656 (bootstrap 95% CI 1.41–1.5212), and p95 latency 50.0. Its correct-success rate fell to 0.695 under worse severity and 0.575 under tight budgets. P4 is a reference upper bound because retryability and fallback quality came from simulator truth and a strict simulator oracle.
