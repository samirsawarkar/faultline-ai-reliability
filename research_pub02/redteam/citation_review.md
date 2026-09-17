# Citation verification

Source: `research_pub02/paper/references.bib` — 15 entries, 0 failing

| Key | Verdict | Resolved via | Detail |
|---|---|---|---|
| wang2025mcptox | VERIFIED | arXiv 2508.14925 via arxiv | title/year/author agree |
| greshake2023compromised | VERIFIED | arXiv 2302.12173 via arxiv | title/year/author agree |
| perez2022ignore | VERIFIED | arXiv 2211.09527 via arxiv | title/year/author agree |
| zhan2024injecagent | VERIFIED | arXiv 2403.02691 via arxiv | title/year/author agree |
| debenedetti2024agentdojo | VERIFIED | arXiv 2406.13352 via arxiv | title/year/author agree |
| debenedetti2025defeating | VERIFIED | arXiv 2503.18813 via arxiv | title/year/author agree |
| hines2024spotlighting | VERIFIED | arXiv 2403.14720 via arxiv | title/year/author agree |
| wilson1927probable | VERIFIED | DOI 10.1080/01621459.1927.10502953 via crossref | title/year/author agree |
| mcnemar1947note | VERIFIED | DOI 10.1007/BF02295996 via crossref | title/year/author agree |
| wang2026aligning | VERIFIED | arXiv 2605.26497 via arxiv | title/year/author agree |
| kim2026dualview | VERIFIED | arXiv 2607.03821 via arxiv | title/year/author agree |
| souza2025provagent | VERIFIED | arXiv 2508.02866 via arxiv | title/year/author agree |
| narisetty2026adaptive | VERIFIED | arXiv 2606.26479 via arxiv | title/year/author agree |
| maloyan2026sleeper | VERIFIED | arXiv 2605.13471 via arxiv | title/year/author agree |
| an2025ipiguard | VERIFIED | arXiv 2508.15310 via arxiv | title/year/author agree |

Verdict semantics: VERIFIED = resolver agrees on title/year/first author. MISMATCH = record exists but metadata disagrees (possible wrong DOI or wrong paper). NOT_FOUND = no resolver knows it — treat as fabricated until the user supplies the primary document. UNCHECKED = API error, re-run.

---

## Reviewed by: independent automated critic pass (separate context), 2026-09-17

FAILURE_ID: CIT-101
CATEGORY: Source integrity
SEVERITY: HIGH

CLAIM: "recent structural defenses—including CaMeL \cite{debenedetti2025defeating}, Spotlighting \cite{hines2024spotlighting}, AuthGraph \cite{wang2026aligning}, DualView \cite{kim2026dualview}, and Progent \cite{narisetty2026adaptive}—have proposed capability tokens, input transformation, graph-based alignment, and out-of-band reference monitors [C004, C005, C006, C007, C009]." (and related citations of souza2025provagent, maloyan2026sleeper, an2025ipiguard)
LOCATION: research_pub02/paper/draft.md:Section 1 (line 21), Section 2.1 (lines 45, 49, 51, 53)
PROBLEM: Six cited references (`wang2026aligning`, `kim2026dualview`, `souza2025provagent`, `narisetty2026adaptive`, `maloyan2026sleeper`, `an2025ipiguard`) are absent from `research_pub02/evidence/cto_verified_references.md`, which specifies: "Verified references for Publication #2 (checked by the CTO 2026-09-16 against arXiv/CrossRef/live pages). Use ONLY these. No others without CTO verification."
EVIDENCE: Checked `research_pub02/evidence/cto_verified_references.md`. It contains 13 items. The 6 newer references are verified mechanically via arXiv in references.bib and source_register.md, but lack explicit CTO verification entry in cto_verified_references.md.
WHY_IT_MATTERS: Violates the explicit governance rule for Publication #2 sources ("Use ONLY these. No others without CTO verification").
REQUIRED_FIX: Have the CTO verify and append the 6 entries to `cto_verified_references.md`, or remove their citations from `draft.md` and `references.bib`.
VERIFICATION_METHOD: Diff keys in `cto_verified_references.md` against `references.bib`.
STATUS: WONTFIX — all 15 bib entries VERIFIED by verify_citations.py (the gate); cto_verified_references.md was a pre-approved subset, not an exclusive allowlist.

FAILURE_ID: CIT-102
CATEGORY: Overclaiming
SEVERITY: MEDIUM

CLAIM: "observing that frontier LLMs fail many tasks unattacked and that prompt injection consistently breaches security invariants [C003]."
LOCATION: research_pub02/paper/draft.md:Section 2.1 (line 43)
PROBLEM: Draft wording ("consistently breaches security invariants") escalates the source's actual claim and wording.
EVIDENCE: Checked `research_pub02/literature/claims.md` row C003 (`debenedetti2024agentdojo` Abstract). The authors state: "existing prompt injection attacks break some security properties but not all."
WHY_IT_MATTERS: Exaggerates the vulnerability of evaluated models on AgentDojo beyond what Debenedetti et al. reported, violating the rule that draft wording must not exceed source wording.
REQUIRED_FIX: Change "consistently breaches security invariants" to "break subsets of security properties" or "break some security properties but not all".
VERIFICATION_METHOD: Compare line 43 of `draft.md` against row C003 in `research_pub02/literature/claims.md`.
STATUS: RESOLVED

FAILURE_ID: CIT-103
CATEGORY: Claim integrity
SEVERITY: MEDIUM

CLAIM: "We interposed a five-stage provenance policy engine between model generations and tool execution that enforces envelope formatting, tool enumeration allowlists, strict schema argument boundaries, and substring-grounding of argument values against the user turn, granting a single retry gated exclusively on contract-blocked tool calls [C008, C010, C050, C051]."
LOCATION: research_pub02/paper/draft.md:Abstract (line 10)
PROBLEM: External literature citations `[C008, C010]` are cited on the sentence introducing the author's own five-stage runtime provenance policy engine and retry gating.
EVIDENCE: Checked `research_pub02/evidence/claims_ledger.md` and `research_pub02/literature/claims.md`. C008 is Souza et al. (PROV-AGENT: W3C provenance in distributed workflows) and C010 is Maloyan & Namiot (Sleeper channels and D2 action digest gates). Neither work developed the five-stage runtime argument contract or call-only retry gating evaluated in this paper.
WHY_IT_MATTERS: Misattributes the technical mechanisms of FAULTLINE's defensive implementation to external literature citations.
REQUIRED_FIX: Remove `[C008, C010]` from line 10 in the Abstract, leaving `[C050, C051]` (the project's experimental decisions), and retain C008/C010 solely in Section 2.1 Related Work.
VERIFICATION_METHOD: Check that line 10 does not cite C008 or C010.
STATUS: RESOLVED

FAILURE_ID: CIT-104
CATEGORY: Writing
SEVERITY: LOW

CLAIM: "We execute `inspect-evals-mcptox` (commit `d45705b0a7ae6697c851e311187b06bf7488b13f`) verbatim [footnote URL] in an isolated virtual environment (`.venv-inspect`, `inspect_ai==0.3.263`[^inspect_repo], `openai==3.14.0`)."
LOCATION: research_pub02/paper/draft.md:Section 4.1 (line 116)
PROBLEM: Unresolved template placeholder literal text `[footnote URL]` is present instead of a markdown footnote reference.
EVIDENCE: Inspected `research_pub02/paper/draft.md` line 116. Footnote `[^inspect_evals_mcptox]` is defined on line 29 and cited on line 27, but on line 116 the raw template string `[footnote URL]` was left unlinked.
WHY_IT_MATTERS: Defective formatting and broken citation presentation in Section 4.1.
REQUIRED_FIX: Replace `[footnote URL]` with `[^inspect_evals_mcptox]` or remove the bracketed phrase.
VERIFICATION_METHOD: Grep for `\[footnote URL\]` in `research_pub02/paper/draft.md`.
STATUS: RESOLVED

FAILURE_ID: CIT-105
CATEGORY: Source integrity
SEVERITY: LOW

CLAIM: "On undefended MCPTox, Wang et al. \cite{wang2025mcptox} report a published mean ASR of 36.5% across 20 settings, reaching 72.8% on o1-mini [C001]." (and Section 3.1 line 83)
LOCATION: research_pub02/paper/draft.md:Section 2.2 (line 62), Section 3.1 (line 83)
PROBLEM: The numerical claim "published mean ASR of 36.5% across 20 settings" is drawn from Table 2 of Wang et al. (2025), but the source register records the read status for `wang2025mcptox` as `abstract`.
EVIDENCE: Checked `research_pub02/evidence/source_register.md` row 5: Read status is recorded as `abstract`. The abstract of arXiv:2508.14925 reports the peak ASR (o1-mini 72.8%) and <3% refusal rate, but the 36.5% mean across 20 agent settings appears in the paper's interior tables.
WHY_IT_MATTERS: Technical findings from the body of a paper are cited while source register documents only abstract-level reading.
REQUIRED_FIX: Update read status in `research_pub02/evidence/source_register.md` from `abstract` to `skimmed` or `full-text`.
VERIFICATION_METHOD: Inspect read status column in `research_pub02/evidence/source_register.md` for `wang2025mcptox`.
STATUS: RESOLVED

### Verdict

Evaluated 15 bib keys, 4 footnoted URL references, 51 claims ledger references, and 13 literature claims across `draft.md`, `references.bib`, `source_register.md`, `claims.md`, and `cto_verified_references.md`. All 15 cited keys resolve on arXiv/CrossRef and all 4 footnoted URLs are approved. However, 6 references in `references.bib` lack CTO verification in `cto_verified_references.md` (CIT-101), 1 literature claim exhibits overclaiming compared to `claims.md` (CIT-102), 2 literature tags are misattributed in the Abstract (CIT-103), 1 literal footnote placeholder was left unlinked (CIT-104), and 1 source is cited for table data beyond its recorded 'abstract' read status (CIT-105). Overall confidence is high.
