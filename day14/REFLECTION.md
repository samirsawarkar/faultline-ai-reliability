# REFLECTION.md — five-minute mission reflection (Day 14)

**Mission.** Make every comparison honest with paired seeds and uncertainty
estimates.
**Fail condition.** You cannot explain or verify the interval and paired test. —
*Not triggered:* every utility is checked against something independent (the Wilson
bounds against the score equation, `norm_ppf`/`chi2_sf`/McNemar-exact against
published values), and both the interval and the paired test are explained in
`LEARN-paired-bootstrap.md` and `INTERPRETATION.md`. See [CHECKPOINT-14.md](CHECKPOINT-14.md).

**Do we need an LLM API now? No.** This is measurement plumbing — intervals and a
paired test — implemented in the standard library so it runs identically everywhere.
Its job is to make every later claim (detection accuracy, recovery-policy
comparisons) carry uncertainty and pass a fair test.

**The sharpest decision.** Verifying Wilson against the score *equation* it solves,
not against a second copy of the closed form (D14-002). Plugging the returned bounds
back into `(p̂−p*)² = z²·p*(1−p*)/n` and getting a residual < 1e-9 is real
verification; re-running the same formula would prove nothing. That is the concrete
answer to "can you verify it?"

**The most useful guardrail.** Exact binomial for small discordant counts (D14-006).
It would have been easy to always use chi-square and quietly over-claim from a
handful of pairs. Making the code report both, prefer the exact test when pairs are
few, and knowing that five one-sided disagreements are *not* significant (p=0.0625),
is the difference between honest and impressive.

**Mastery gate.**
- *Explain* — [LEARN-paired-bootstrap.md](LEARN-paired-bootstrap.md) +
  [`INTERPRETATION.md`](evidence/INTERPRETATION.md).
- *Build* — Wilson, bootstrap, McNemar, math primitives (stdlib only).
- *Debug* — [`evidence/edge_cases.json`](evidence/edge_cases.json): every boundary.
- *Measure* — [`evidence/paired_comparison.json`](evidence/paired_comparison.json).
- *Defend* — [`evidence/stats_verification.json`](evidence/stats_verification.json) +
  [DECISIONS.md](DECISIONS.md), D14-001…D14-007.

**What I'd watch next.** Mission 15 (Q2) uses exactly these tools: it reports
detection accuracy per fault family on the Day-13 held-out split with Wilson
intervals, and compares detectors with McNemar — the split hypothesis from Day 11
finally measured with uncertainty instead of point estimates.
