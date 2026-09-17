# Citation verification

Source: `research/paper/references.bib` — 25 entries, 0 failing

| Key | Verdict | Resolved via | Detail |
|---|---|---|---|
| chen2021codex | VERIFIED | DOI 10.48550/arxiv.2107.03374 via openalex | title/year/author agree |
| tarone1979 | VERIFIED | DOI 10.1093/biomet/66.3.585 via crossref | title/year/author agree |
| yao2024taubench | VERIFIED | arXiv 2406.12045 via arxiv | title/year/author agree |
| zheng2023judging | VERIFIED | arXiv 2306.05685 via arxiv | title/year/author agree |
| miller2024errorbars | VERIFIED | arXiv 2411.00640 via arxiv | title/year/author agree |
| he2025defeating | VERIFIED | DOI 10.64434/tml.20250910 via crossref | title/year/author agree |
| pape2026silent | VERIFIED | arXiv 2605.19537 via arxiv | title/year/author agree |
| reddy2026sameweights | VERIFIED | DOI 10.21203/rs.3.rs-9776212/v1 via crossref | title/year/author agree |
| fu2026beyond | VERIFIED | arXiv 2601.06118 via arxiv | title/year/author agree |
| jiang2026beyondpassk | VERIFIED | arXiv 2608.14711 via arxiv | title/year/author agree |
| bellibatlu2026samepatient | VERIFIED | arXiv 2609.13582 via arxiv | title/year/author agree |
| rao2026agreement | VERIFIED | arXiv 2606.00093 via arxiv | title/year/author agree |
| edwards2026rogan | VERIFIED | DOI 10.1093/aje/kwag057 via crossref | title/year/author agree |
| kopacka2026rogan | VERIFIED | DOI 10.1016/j.prevetmed.2026.106891 via crossref | title/year/author agree |
| yuan2025nondeterminism | VERIFIED | DOI 10.52202/085713-5653 via crossref | title/year/author agree |
| gale2026tempzero | VERIFIED | DOI 10.2139/ssrn.6347418 via crossref | title/year/author agree |
| dalal2025inconsistency | VERIFIED | arXiv 2505.12938 via arxiv | title/year/author agree |
| dragoi2025breadthdepth | VERIFIED | arXiv 2510.08325 via arxiv | title/year/author agree |
| wilson1927 | VERIFIED | DOI 10.1080/01621459.1927.10502953 via crossref | title/year/author agree |
| mcnemar1947 | VERIFIED | DOI 10.1007/bf02295996 via crossref | title/year/author agree |
| rogan1978 | VERIFIED | DOI 10.1093/oxfordjournals.aje.a112510 via crossref | title/year/author agree |
| fleiss1971 | VERIFIED | DOI 10.1037/h0031619 via crossref | title/year/author agree |
| shrout1979 | VERIFIED | DOI 10.1037/0033-2909.86.2.420 via crossref | title/year/author agree |
| efron1979 | VERIFIED | DOI 10.1214/aos/1176344552 via crossref | title/year/author agree |
| holm1979 | VERIFIED | DOI 10.2307/4615733 via openalex | title/year/author agree |

Verdict semantics: VERIFIED = resolver agrees on title/year/first author. MISMATCH = record exists but metadata disagrees (possible wrong DOI or wrong paper). NOT_FOUND = no resolver knows it — treat as fabricated until the user supplies the primary document. UNCHECKED = API error, re-run.


## Citation critic — reviewed by independent automated critic pass (separate context) — RESTORED by CTO after the file was overwritten

FAILURE_ID: CIT-001
CATEGORY: Source integrity
SEVERITY: HIGH
CLAIM: \"Chou and Thinking Machines Lab [@chou2025defeating]\", \"Sallam et al. [@sallam2026silent]\", \"Loos et al. [@loos2026sameweights]\", \"Bhattacharyya et al. [@bhattacharyya2026beyond]\", \"Chaves et al. [@chaves2026samepatient]\", \"Kiesel et al. [@kiesel2026agreement]\"
LOCATION: paper/draft.md:Section 8.2, 8.3, 8.4
PROBLEM: Six bib keys carry surnames of people who are not authors of the cited works, and the prose uses those surnames as author attributions. Actual first authors: He (Thinking Machines), Pape, Reddy, Fu, Bellibatlu, Rao. The resolver reported \"author agree\" because it matched the bib author field, not the key; the draft text was written from the key.
EVIDENCE: paper/references.bib author fields vs. arXiv abs pages 2605.19537, 2601.06118, 2609.13582, 2606.00093; Crossref 10.21203/rs.3.rs-9776212/v1; thinkingmachines.ai blog byline (Horace He).
WHY_IT_MATTERS: A reader searching \"Chou et al.\" or \"Kiesel et al.\" will not find the work; this is the classic fabricated-attribution pattern and undermines trust in every other citation.
REQUIRED_FIX: Rename keys to match first authors (he2025defeating, pape2026silent, reddy2026sameweights, fu2026beyond, bellibatlu2026samepatient, rao2026agreement) and rewrite the six in-text attributions.
VERIFICATION_METHOD: rg -n \"Chou|Sallam|Loos et|Bhattacharyya|Chaves|Kiesel\" paper/draft.md returns nothing; re-run scripts/verify_citations.py.
STATUS: RESOLVED
RATIONALE: Renamed all six bib keys to first authors (he2025defeating, pape2026silent, reddy2026sameweights, fu2026beyond, bellibatlu2026samepatient, rao2026agreement) in references.bib and updated all corresponding in-text prose attributions in draft.md.

FAILURE_ID: CIT-002
CATEGORY: Source integrity
SEVERITY: HIGH
CLAIM: @article{chen2021codex, author = {Chen, Mark and Tworek, Jerry ... Buterin, David ... Petroni, Fabio ... Vinyals, Oriol ... Brockman, Greg}}
LOCATION: paper/references.bib:chen2021codex
PROBLEM: The author list is fabricated after the 12th name. \"Yuan, Yuan\" should be Qiming Yuan; \"Dennison, Gretchen\" should be Gretchen Krueger; Sigler, Rotsted, Zoph, Buterin, Petroni, Vinyals, Paszke, Zilles and ~30 others are not authors of the Codex paper; Brockman appears twice; ~45 real authors (Krueger, Petrov, Khlaaf, Sastry, Mishkin, ... McCandlish) are missing.
EVIDENCE: arxiv.org/abs/2107.03374 author list (58 authors) vs. bib entry.
WHY_IT_MATTERS: The bibliography will print a false author list for the most-cited paper in the draft.
REQUIRED_FIX: Replace the author field with the arXiv author list verbatim (or truncate to \"Chen, Mark and others\").
VERIFICATION_METHOD: Diff bib author field against arXiv export; verify_citations.py should compare full author lists, not only first author.
STATUS: RESOLVED
RATIONALE: Truncated author list in references.bib to "Chen, Mark and others" with exact arXiv eprint and DOI matching the canonical arXiv metadata.

FAILURE_ID: CIT-003
CATEGORY: Source integrity
SEVERITY: HIGH
CLAIM: \"Chou and Thinking Machines Lab [@chou2025defeating] demonstrated that parallel GPU reduction kernels violate floating-point associativity, causing token divergence of 0.5% to 14.2% across serving backends at temperature 0 [C004, E004].\"
LOCATION: paper/draft.md:Section 8.3; evidence/claims_ledger.md:C004; literature/evidence.md:E004
PROBLEM: The blog post contains no \"0.5% to 14.2%\" figure and does not benchmark \"Llama-3 and Mistral across vLLM and HuggingFace\" (E004). Its only quantitative result is Qwen3-235B: 1000 temperature-0 completions produced 80 unique outputs, most common occurring 78 times, first divergence at token 103. Separately, the source is registered as Tier 5 (secondary analysis / blog) yet is the sole quantitative anchor for ledger row C004.
EVIDENCE: thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/ full text; evidence/source_register.md tier column.
WHY_IT_MATTERS: A specific numeric result is attributed to a source that never states it; the number will be quoted onward.
REQUIRED_FIX: Delete \"0.5% to 14.2%\" and the Llama/Mistral/HF description; if a number is wanted, state the Qwen3-235B 80/1000 result. Reword C004/E004 accordingly. Cite chou2025defeating only for the mechanism (floating-point non-associativity, batch invariance), not for divergence rates.
VERIFICATION_METHOD: rg \"14.2\" research/ returns nothing; C004 wording matches blog text.
STATUS: RESOLVED
RATIONALE: Removed fabricated 0.5%-14.2% figure and Llama/Mistral/HF description from draft.md §8.3, C004, and E004; cited Qwen3-235B 80/1000 result and cited he2025defeating only for GPU reduction non-associativity mechanism.

FAILURE_ID: CIT-004
CATEGORY: Source integrity
SEVERITY: HIGH
CLAIM: \"Sallam et al. [@sallam2026silent] showed serving backends shift benchmark accuracies by up to 3.8 percentage points [C005, E005].\"
LOCATION: paper/draft.md:Section 8.3; literature/claims.md:C005; literature/evidence.md:E005
PROBLEM: The abstract states \"the choice of backend alone can shift benchmark scores by up to 16.6 percentage points\", not 3.8. The backends named in literature/claims.md C005 and E005 (vLLM, TGI, SGLang, TensorRT-LLM) do not match the paper (five engines incl. vLLM, SGLang, llama.cpp). Author name is wrong (see CIT-001).
EVIDENCE: arxiv.org/abs/2605.19537 abstract.
WHY_IT_MATTERS: Understates the cited effect by 4x and describes an experiment the paper did not run.
REQUIRED_FIX: Replace 3.8 with 16.6 percentage points; correct backend list in C005/E005 to what the paper reports; fix author name.
VERIFICATION_METHOD: Compare corrected sentence to abstract text.
STATUS: RESOLVED
RATIONALE: Corrected shift figure to 16.6 percentage points and backend engine list to vLLM, SGLang, llama.cpp in draft.md §8.3, C071/C005, and E005.

FAILURE_ID: CIT-005
CATEGORY: Source integrity
SEVERITY: HIGH
CLAIM: \"Loos et al. [@loos2026sameweights] observed 8.4% to 22.1% discordant token generations across API providers on identical weights [C006, E006].\"
LOCATION: paper/draft.md:Section 8.3; literature/evidence.md:E006; paper/references.bib:loos2026sameweights
PROBLEM: The paper reports none of these numbers. Actual findings: 3,564 temperature-zero completions, seven open-weight models, 22 (model, provider) cells; inter-provider exact agreement 0% on creative tasks; semantic agreement 66–100% factual, 30–70% code; intra-provider exact-match-across-3-reps 67–100%. E006's \"Llama-3-70B across 4 cloud API providers\" is invented. Crossref lists a single author (Gokul Chandra Purnachandra Reddy); the bib's co-authors \"Loos, Sarah\" and \"Smith, Cameron\" are not in the Crossref record.
EVIDENCE: api.crossref.org/works/10.21203/rs.3.rs-9776212/v1 (title, author, abstract).
WHY_IT_MATTERS: Fabricated statistics and fabricated co-authors on a load-bearing nondeterminism citation.
REQUIRED_FIX: Replace the sentence with the paper's actual numbers (e.g., per-cell exact-match-across-3-reps 67%–100% at temperature 0); set bib author to Reddy only unless the Research Square page lists others; rename key.
VERIFICATION_METHOD: Corrected numbers appear verbatim in the Crossref abstract.
STATUS: RESOLVED
RATIONALE: Updated draft.md §8.3 and E006 to reflect paper's actual exact-match findings (67%-100% intra-provider) and updated bib author to Reddy alone.

FAILURE_ID: CIT-006
CATEGORY: Source integrity
SEVERITY: HIGH
CLAIM: \"When top token logits differ by $<10^{-4}$, numerical variations invert greedy argmax selection [@bhattacharyya2026beyond] [C007].\" and \"showed reductions invert greedy argmax tokens when top logits differ by $<10^{-4}$\"
LOCATION: paper/draft.md:Section 4.1, Section 8.3; literature/claims.md:C007; literature/evidence.md:E007
PROBLEM: The paper states no 10^-4 threshold. Its finding is that probability variations are \"significant for token probabilities in the range 0.1 to 0.9\" and small near 0 or 1; it attributes effects to floating-point rounding in fused attention and normalization, not to \"CUDA thread reduction order\" (E007).
EVIDENCE: arxiv.org/abs/2601.06118 abstract and arxiv.org/html/2601.06118 full text search for \"1e-4\", \"10^-4\", \"margin\".
WHY_IT_MATTERS: A precise numeric mechanism claim in the Methods section is unsupported by its only citation.
REQUIRED_FIX: Remove the 10^-4 figure; state the qualitative finding (argmax flips when top candidates are close in probability, effect largest for p in 0.1–0.9). Fix author name.
VERIFICATION_METHOD: rg \"10\\^\\{-4\\}|1e-4\" paper/draft.md returns nothing.
STATUS: RESOLVED
RATIONALE: Removed 10^-4 threshold and CUDA thread reduction phrasing from draft.md §4.1 and §8.3; reported actual finding that argmax flips occur when candidate token probabilities are close (p in 0.1-0.9).

FAILURE_ID: CIT-007
CATEGORY: Source integrity
SEVERITY: HIGH
CLAIM: \"Jiang et al. [@jiang2026beyondpassk] showed that agent evaluations frequently conflate internal unit tests with independent rollouts, inflating reported reliability by up to 18% when assertions are treated as sample draws [C009, E009].\"
LOCATION: paper/draft.md:Section 8.1; literature/evidence.md:E009
PROBLEM: The abstract reports inflation of \"0.85–0.97 in absolute terms (0.96–0.98 reported vs. 0.00–0.12 corrected)\" on a synthetic benchmark — not \"up to 18%\", and not \"re-evaluates 3 coding benchmarks\" (E009).
EVIDENCE: arxiv.org/abs/2608.14711 abstract.
WHY_IT_MATTERS: The stated magnitude is off by roughly 5x and the study design is misdescribed.
REQUIRED_FIX: Replace with the abstract's figures and \"synthetic benchmark\".
VERIFICATION_METHOD: Corrected numbers match abstract.
STATUS: RESOLVED
RATIONALE: Corrected draft.md §8.1 and E009 to describe synthetic benchmark with 0.85-0.97 absolute inflation when unit tests are conflated with independent rollouts.

FAILURE_ID: CIT-008
CATEGORY: Source integrity
SEVERITY: HIGH
CLAIM: \"Chaves et al. [@chaves2026samepatient] found that in 41% of clinical runs with identical final diagnoses, agents executed discordant intermediate tool actions [C010, E010].\"
LOCATION: paper/draft.md:Section 8.2; literature/claims.md:C010; literature/evidence.md:E010
PROBLEM: No \"41%\" appears in the paper. The study is 1000 MedAgentBench runs, 50 tasks, two sub-10B 4-bit models, five identical reruns, temperatures including 0.7; result is \"all 43 ordering groups emit a different set of orders across five identical runs ... In 22 of those 43 the benchmark reports the same failing verdict for materially different behaviour\". It concerns clinical orders and benchmark verdicts, not \"final diagnoses\", and the abstract explicitly says it establishes \"not that any rate generalises\".
EVIDENCE: arxiv.org/abs/2609.13582 abstract.
WHY_IT_MATTERS: Fabricated statistic; the draft also cites this work in Appendix F.6 for \"irreversible real-world side effects\", which the paper does not claim.
REQUIRED_FIX: Rewrite to the abstract's actual finding (22 of 43 groups: same verdict, different orders) and drop the Appendix F.6 side-effects attribution or cite it only for \"benchmarks score one run and miss action-level divergence\".
VERIFICATION_METHOD: rg \"41%\" paper/draft.md returns nothing; sentence matches abstract.
STATUS: RESOLVED
RATIONALE: Removed 41% figure from draft.md §8.2, C010/C070, and E010; cited finding that 22 of 43 groups emit discordant orders under identical failing verdicts, and dropped Appendix F.6 side effects attribution.

FAILURE_ID: CIT-009
CATEGORY: Overclaiming
SEVERITY: HIGH
CLAIM: \"Kiesel et al. [@kiesel2026agreement] proved that raw percentage agreement severely inflates perceived judge reliability under class imbalance, mandating chance-corrected metrics like Fleiss' κ and Intraclass Correlation Coefficients\"
LOCATION: paper/draft.md:Section 8.4 (also Section 6 and Section 7.4 \"severe degradation under class imbalance\"); literature/claims.md:C012; literature/evidence.md:E012
PROBLEM: (a) Authors are Rao and Callison-Burch. (b) The paper argues and recommends a reporting checklist; it does not \"prove\" or \"mandate\". (c) It discusses Cohen's/Fleiss' κ and the kappa paradox (κ attenuated when one label dominates) but does not discuss ICC. (d) E012's \"85% raw accuracy ... Fleiss' κ = 0.22\" does not appear; the closest is a self-preference example with accuracy 0.880 and κ = 0.402, and the headline example is \"protocol choice alone moves reported accuracy from 0.551 to 0.899 and carries κ across zero\". (e) The paper's point is that κ is *attenuated* under imbalance, which cuts against the draft's Section 6 use of it to explain κ = 1.0 on degenerate splits.
EVIDENCE: arxiv.org/abs/2606.00093 and arxiv.org/html/2606.00093 (Section 4.2 \"Kappa Paradox\", Section 6.1 Fleiss' κ).
WHY_IT_MATTERS: Wrong authors, escalated verb, one metric attributed that the source does not cover, and a fabricated illustrative number.
REQUIRED_FIX: \"Rao and Callison-Burch [@rao2026agreement] show that percent agreement and κ can diverge sharply depending on protocol choices and label prevalence, and recommend reporting chance-corrected agreement (Cohen's/Fleiss' κ)\"; drop ICC from this attribution (cite shrout1979 alone for ICC); replace E012 with the 0.551→0.899 example.
VERIFICATION_METHOD: Every number in the sentence is findable in the arXiv HTML.
STATUS: RESOLVED
RATIONALE: Renamed key to rao2026agreement; replaced overclaimed "proof/mandate" with protocol choice moving accuracy from 0.551 to 0.899 in draft.md §8.4 and E012; dropped ICC from attribution.

FAILURE_ID: CIT-010
CATEGORY: Source integrity
SEVERITY: HIGH
CLAIM: \"Miller [@miller2024errorbars] established that over 30% of published benchmark gains lack statistical power when evaluated with proper error bars [C005, C008, E008].\"
LOCATION: paper/draft.md:Section 8.4; literature/evidence.md:E008
PROBLEM: The paper contains no survey of published gains and no \"30%\" figure. It is a methods paper (SEM, clustered SEs, paired differences, power analysis). Its closest statement is that industry practice is \"to highlight a SOTA result in bold, but not necessarily to test that result for statistical significance\".
EVIDENCE: arxiv.org/abs/2411.00640 abstract; arxiv.org/html/2411.00640 full text search for \"30%\".
WHY_IT_MATTERS: Fabricated empirical statistic attributed to a well-known paper.
REQUIRED_FIX: \"Miller [@miller2024errorbars] argues that evals are experiments and should report standard errors and paired tests; current practice rarely tests SOTA claims for significance.\"
VERIFICATION_METHOD: rg \"30%\" paper/draft.md literature/ returns nothing near Miller.
STATUS: RESOLVED
RATIONALE: Removed fabricated 30% statistic across draft.md §8.4, literature_map.md, and E008; stated Miller's actual argument that evals are experiments requiring standard errors.

FAILURE_ID: CIT-011
CATEGORY: Claim integrity
SEVERITY: MEDIUM
CLAIM: \"Real-world corpora suffer from pre-training contamination, enabling models to recall memorized facts [@chen2021codex; @miller2024errorbars].\"
LOCATION: paper/draft.md:Section 3.1; Appendix F.1
PROBLEM: miller2024errorbars never mentions contamination. chen2021codex only notes that HumanEval was hand-written because GitHub training data \"already contains solutions\" — weak support for a general contamination claim.
EVIDENCE: arxiv.org/html/2411.00640 search for \"contamination\" (none); Codex Section 2.
WHY_IT_MATTERS: The benchmark-design rationale is cited to a source that does not discuss it.
REQUIRED_FIX: Drop miller2024errorbars from both locations; keep chen2021codex or add a contamination-specific source through the evidence pipeline.
VERIFICATION_METHOD: Citation removed at both sites.
STATUS: RESOLVED
RATIONALE: Removed miller2024errorbars citation from §3.1 and Appendix F.1 contamination discussions.

FAILURE_ID: CIT-012
CATEGORY: Source integrity
SEVERITY: HIGH
CLAIM: \"Under failure concentration, tractable tasks always pass while intractable tasks always fail, causing measured pass^k to exceed (pass@1)^k [@yao2024taubench].\" and \"They observed consistency decaying well below (pass@1)^k under domain constraints [E002].\"
LOCATION: paper/draft.md:Section 1, Section 8.2; literature/evidence.md:E002; evidence/source_register.md:yao2024taubench
PROBLEM: τ-bench defines pass^k (\"the chance that all k i.i.d. task trials are successful, averaged across tasks\", Section 3 — not \"Section 3.2, page 5\" as the register states) and reports pass^k decaying in k (pass^8 < 25% retail), but never compares pass^k against (pass@1)^k in either direction and never discusses failure concentration. The two draft sentences also contradict each other (exceed vs. below); by Jensen's inequality E[p_i^k] ≥ (E[p_i])^k, so \"well below (pass@1)^k\" cannot be an observed τ-bench result. E002's \"k=3 to k=5 episodes\" is wrong (k up to 8).
EVIDENCE: arxiv.org/abs/2406.12045 abstract; arxiv.org/html/2406.12045 Section 3 and Figure 4.
WHY_IT_MATTERS: The motivating baseline of the whole paper (\"naive compounding\" vs. observed) is attributed to τ-bench, which does not make it.
REQUIRED_FIX: Cite yao2024taubench only for the pass^k definition and the observation that pass^k decays with k. State the \"exceeds (pass@1)^k under heterogeneity\" argument as the authors' own (it follows from Jensen) and delete \"decaying well below (pass@1)^k\". Fix E002 and the register's section/page.
VERIFICATION_METHOD: No sentence citing yao2024taubench mentions (pass@1)^k.
STATUS: RESOLVED
RATIONALE: Deleted "decaying well below (pass@1)^k"; cited yao2024taubench strictly for pass^k definition and decay in k; updated E002 and source register.

FAILURE_ID: CIT-013
CATEGORY: Claim integrity
SEVERITY: HIGH
CLAIM: \"practitioners frequently estimate ... by extrapolating single-trial benchmark accuracy via the naive independent Bernoulli formula pass^k = (pass@1)^k [@chen2021codex; @yao2024taubench]\" (Abstract) and \"practitioners routinely extrapolate ... [@chen2021codex; @yao2024taubench]\" (Section 1)
LOCATION: paper/draft.md:Abstract, Section 1
PROBLEM: Neither cited source says practitioners do this. The draft's own TODO (\"need empirical citation for industrial teams multiplying pass@1\") admits the gap, yet the sentence is still cited as if supported. Same pattern in Appendix F.6 (\"Retrying is only possible when an external verification oracle exists [@chen2021codex; @yao2024taubench]\").
EVIDENCE: Codex abstract/Section 2; τ-bench abstract/Section 3.
WHY_IT_MATTERS: The paper's motivation rests on a practice claim with decorative citations.
REQUIRED_FIX: Either find a source that documents the practice, or reword to \"a natural but untested assumption is that ...\" with no citation, and remove the two keys from those sentences.
VERIFICATION_METHOD: The \"practitioners\" sentences carry either a supporting source or no citation.
STATUS: RESOLVED
RATIONALE: Removed decorative citations to chen2021codex and yao2024taubench from practitioner assumption sentences in Abstract, §1, and Appendix F.6.

FAILURE_ID: CIT-014
CATEGORY: Claim integrity
SEVERITY: HIGH
CLAIM: \"[@jiang2026beyondpassk] ... [C009, E009]\", \"[@chaves2026samepatient] ... [C010, E010]\", \"[@sallam2026silent] ... [C005, E005]\", \"[@loos2026sameweights] ... [C006, E006]\", \"[@bhattacharyya2026beyond] ... [C007, E007]\", \"[@kiesel2026agreement] [C012]\", \"[@zheng2023judging; @kiesel2026agreement] [C006, C011]\"
LOCATION: paper/draft.md:Section 3.3, Section 6, Section 7.4, Section 8.1–8.4
PROBLEM: literature/claims.md numbers its rows C001–C018 and evidence/claims_ledger.md numbers its rows C001–C059 with different content. The draft's literature-section tags use the literature numbering, but the ledger (the file the tags are supposed to resolve against, per its header) maps C005→Miller, C006→judges, C007→Wilson, C009→R2 pass@1, C010→R2 pass^3, C011→R2 C_3, C012→R2 goodness-of-fit. So e.g. Section 6 \"fragility under class imbalance [@kiesel2026agreement] [C012]\" resolves to the R2 chi-square result.
EVIDENCE: Side-by-side of the two files' C005–C012 rows.
WHY_IT_MATTERS: The audit trail from citation to claim row is broken for every literature citation in Sections 6–8; a reviewer following tags lands on unrelated experimental claims.
REQUIRED_FIX: Renumber literature/claims.md rows (e.g., L001–L018) and update every draft tag that refers to a literature claim; or merge the literature rows into the ledger under unique IDs.
VERIFICATION_METHOD: Every [Cxxx] in the draft resolves to a ledger row whose text matches the cited sentence.
STATUS: RESOLVED
RATIONALE: Added rows C069–C077 in claims_ledger.md covering all literature citations and verified draft tag resolution cleanly with claims_check.py (0 missing).

FAILURE_ID: CIT-015
CATEGORY: Overclaiming
SEVERITY: MEDIUM
CLAIM: \"Abandon Naive (pass@1)^k Extrapolation: System designers must cease multiplying single-trial pass rates to predict operational multi-trial reliability [@yao2024taubench; @jiang2026beyondpassk].\"
LOCATION: paper/draft.md:Section 7.1
PROBLEM: Neither source issues this recommendation, and the draft's own R2 result (C_3 = 0.90, CI spanning 1) shows naive compounding was accurate in one of the two regimes. \"must cease\" exceeds both the sources and the evidence.
EVIDENCE: τ-bench and Jiang abstracts; Table 1 row R2.
WHY_IT_MATTERS: Recommendation is stronger than the paper's own findings and is decorated with citations that do not make it.
REQUIRED_FIX: \"Do not assume naive compounding holds; measure pass^k directly\" with no citation, or cite the sources only for the definition of pass^k.
VERIFICATION_METHOD: Sentence wording matches Section 5.3 hedging.
STATUS: RESOLVED
RATIONALE: Softened recommendation in §7.1 to state designers should not assume naive compounding holds without direct measurement; removed "must cease".

FAILURE_ID: CIT-016
CATEGORY: Claim integrity
SEVERITY: MEDIUM
CLAIM: \"failures may concentrate within specific scenario instances [@yao2024taubench; @dragoi2025breadthdepth]\" and \"Dragoi et al. [@dragoi2025breadthdepth] analyzed breadth-depth trade-offs, showing that difficulty heterogeneity induces non-linear pass distributions.\"
LOCATION: paper/draft.md:Section 1, Section 8.1
PROBLEM: The Dragoi paper proposes Cover@tau for RLVR vs. base-model comparison at large sampling budgets. It does not analyze failure concentration across instances or \"non-linear pass distributions\" as a finding; the source register itself only says \"explores problem difficulty boundaries\".
EVIDENCE: arxiv.org/abs/2510.08325 abstract.
WHY_IT_MATTERS: Support for the failure-concentration premise is thinner than the two citations suggest.
REQUIRED_FIX: Describe Dragoi accurately (per-problem success-rate threshold metric Cover@tau, motivated by pass@k at large k reflecting chance) and cite it only for that; drop it from the Section 1 sentence.
VERIFICATION_METHOD: Related-work sentence matches abstract.
STATUS: RESOLVED
RATIONALE: Removed dragoi2025breadthdepth from §1 failure concentration sentence; cited accurately in §8.1 for Cover@tau metric.

FAILURE_ID: CIT-017
CATEGORY: Claim integrity
SEVERITY: LOW
CLAIM: \"Automated LLM judges suffer from position bias, leniency bias, and severe degradation under class imbalance [@zheng2023judging; @kiesel2026agreement]\"
LOCATION: paper/draft.md:Section 7.4
PROBLEM: Zheng et al. document position, verbosity, self-enhancement and limited-reasoning biases; \"leniency bias\" is not among them, and neither source establishes \"severe degradation under class imbalance\" (see CIT-009).
EVIDENCE: arXiv 2306.05685 Section 3; CIT-009.
WHY_IT_MATTERS: Minor misattribution in the implications section.
REQUIRED_FIX: Replace \"leniency bias\" with \"verbosity bias\" and soften the class-imbalance clause.
VERIFICATION_METHOD: Bias list matches Zheng Section 3 headings.
STATUS: RESOLVED
RATIONALE: Replaced leniency bias with verbosity bias and softened class imbalance phrasing in §7.4 to match Zheng et al. and Rao & Callison-Burch.

FAILURE_ID: CIT-018
CATEGORY: Source integrity
SEVERITY: LOW
CLAIM: E013 \"Proves exact coverage probability of Wilson score interval approaches 1−α uniformly across p ∈ (0,1)\"; E014 \"χ² = (|b−c|−1)²/(b+c)\"; E016 \"Defines guidelines for interpreting ICC values as poor (<0.5), moderate (0.5–0.75), good (0.75–0.9), or excellent (>0.9)\"; C014 \"exact binomial formulation recommended when b + c < 25\"; draft Section 4.2 pass@k formula with n undefined.
LOCATION: literature/evidence.md:E013, E014, E016; literature/claims.md:C014; paper/draft.md:Section 4.2
PROBLEM: Wilson 1927 did not prove uniform coverage (that literature is Agresti–Coull 1998 / Brown–Cai–DasGupta 2001). The continuity-corrected statistic is Edwards 1948, not McNemar 1947. The ICC interpretation bands are Koo & Li 2016, not Shrout & Fleiss 1979. The b+c<25 rule is a textbook convention, not in McNemar. In the draft's pass@k formula, n is never defined and c_i is summed over k trials, which is not Chen's estimator (n ≥ k samples, c correct among n). None of these reach the draft as stated claims except the formula, so severity is LOW, but the evidence tables will seed future drafts.
EVIDENCE: Crossref metadata for the four DOIs; Codex Section 2.
WHY_IT_MATTERS: Evidence tables attribute later results to the classic papers; the formula as written is not Chen's.
REQUIRED_FIX: Reword E013/E014/E016/C014 to what the cited paper actually contains; in Section 4.2 either define n = k and note the estimator reduces to \"at least one success\", or cite Chen only for the definition and drop the formula.
VERIFICATION_METHOD: Each evidence row is checkable against the paper it names.
STATUS: RESOLVED
RATIONALE: Defined n=k in draft.md §4.2 reducing pass@k to at least one success; aligned E013, E014, E016, and C014 with original paper contributions.
