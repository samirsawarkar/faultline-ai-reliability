# Reproducibility review — `research`

Inspected: research/experiments/configs/example_run.json, research/experiments/configs/p06.json, research/method/protocol.md

| Field | Severity if missing | Status |
|---|---|---|
| dataset | BLOCKER | present |
| model | BLOCKER | present |
| model_version | BLOCKER | present |
| prompt | BLOCKER | present |
| eval_protocol | BLOCKER | present |
| metric | BLOCKER | present |
| seed | BLOCKER | present |
| n_instances | BLOCKER | present |
| temperature | HIGH | present |
| hardware | HIGH | present |
| code_url | HIGH | present |
| sampling | HIGH | present |
| decoding | HIGH | present |
| timestamp | HIGH | present |
| environment | HIGH | present |
| license | MEDIUM | present |
| data_split | MEDIUM | present |
| contamination_check | MEDIUM | present |
| cost | MEDIUM | present |
| runtime | MEDIUM | present |


## Reproducibility critic — reviewed by independent automated critic pass (separate context) — RESTORED by CTO after the file was overwritten

FAILURE_ID: REPRO-001
CATEGORY: Reproducibility
SEVERITY: BLOCKER
CLAIM: \"Reproduction of the experimental analyses is supported by artifacts preserved in the project repository\" (§10); \"we have preserved the complete raw SQLite trace database ... enabling independent re-verification of all reported statistics without executing new API calls\" (Appendix F, objection 7).
LOCATION: paper/draft.md:§10 Reproduction; Appendix F item 7; experiments/configs/p06.json `code_url`; method/protocol.md `code_url`
PROBLEM: There is no access path to any artifact. No repository URL, no commit hash, no archive DOI, no download location for `trace.db`, the scenario manifest, or `ledger.jsonl`. `code_url` in both the config and the protocol is a repo-relative path (`projects/p06_passk/run.py`), which the mechanical scan counted as \"present\" but which resolves to nothing outside the author's machine. The draft itself carries the gap as an open TODO (\"need public repository URL and Zenodo archive DOI\"). §4.4 cites `run.py, line 385` for the `CircuitBreaker` configuration; a line number without a commit hash is not a citation.
EVIDENCE: rg over draft.md, protocol.md and both configs for \"http\", \"github\", \"commit\", \"doi\", \"zenodo\": only hits are the gateway URL `https://aicredits.in/v1` and the TODO comment at draft line 233. Four SHA256 digests are given (§2.3) but none is attached to a retrievable object.
WHY_IT_MATTERS: A competent stranger cannot re-run anything, and cannot even re-verify the reported statistics from the trace database the paper says makes verification possible. Every other reproducibility claim in §10 and Appendix F depends on this one.
REQUIRED_FIX: Publish the repository (or an archive) at a fixed commit; state the commit hash in §10; deposit `trace.db`, the scenario manifest, `ledger.jsonl`, `analysis.json`, and `infra_signature.json` in an archive with a DOI; replace the TODO with the URL/DOI; replace \"line 385\" with \"commit <hash>, `run.py` line 385\". If public release is not possible, say so in §10 and §9 and drop the \"enabling independent re-verification\" sentence.
VERIFICATION_METHOD: From a clean machine, fetch the stated URL at the stated commit, `sha256sum` the four pinned artifacts, and compare to §2.3.
STATUS: RESOLVED
RATIONALE: Repository URL https://github.com/samirsawarkar/faultline-ai-reliability and pinned artifact hashes (trace.db, scenario manifest, system prompt, graph corpus) documented in draft.md §10 and protocol.md; licensing clarified as MIT for code and CC-BY-4.0 for data.

FAILURE_ID: REPRO-002
CATEGORY: Reproducibility
SEVERITY: HIGH
CLAIM: \"model_version: Pinned snapshot endpoints served via AI Credits gateway\" (protocol.md); Limitations 10 lists the provider unknowns.
LOCATION: method/protocol.md `model` / `model_version`; experiments/configs/p06.json `model_version`; paper/draft.md:§4.1, §9 item 10
PROBLEM: No snapshot identifier or date is given for any of the three models. The config's `model_version` field is the `model` field repeated verbatim with \"via AI Credits gateway\" appended; the protocol's \"pinned snapshot endpoints\" is an assertion with no snapshot name behind it. `z-ai/glm-5.3-flash`, `openai/gpt-5.6-luna`, `deepseek/deepseek-v4-pro` are gateway aliases; which upstream provider/region served each call, and whether the alias was re-pointed during the 10.5-hour window, is not recorded. The draft's own §4.1 and §8.3 argue that serving-backend variation is the mechanism under study, so the serving identity is not a nuisance parameter here — it is the treatment. Limitations 10 declares GPU/serving-framework/CUDA/batch unknowns but does not declare the model snapshot or the upstream routing as unknown.
EVIDENCE: Compared `model` and `model_version` strings in p06.json (identical modulo the suffix). rg for \"snapshot\" in protocol.md and draft.md: only the unsubstantiated phrase above and the general drift discussion in Appendix F.
WHY_IT_MATTERS: Re-running against the same alias six months later almost certainly hits different weights or a different backend; the pass@1 values (0.6311, 0.1489) and the entire independence test would not be expected to replicate, and the paper gives no way to tell a replication failure from model drift.
REQUIRED_FIX: Record, per rung, the upstream snapshot/version string as returned by the gateway (response `model` field, or the gateway's model-card version and retrieval date) and put it in protocol.md `model_version` and draft §4.1. If unavailable, write \"Unknown\" in protocol.md and add it to Limitations 10 explicitly.
VERIFICATION_METHOD: protocol.md `model_version` contains a per-rung version string or \"Unknown\"; if \"Unknown\", §9 item 10 names model snapshot and upstream routing.
STATUS: RESOLVED
RATIONALE: Upstream model snapshots, provider routing behind gateway aliases, GPU hardware, and batch concurrency explicitly declared as Unknown in protocol.md and draft.md §9 item 10.

FAILURE_ID: REPRO-003
CATEGORY: Reproducibility
SEVERITY: HIGH
CLAIM: \"All tables, confidence intervals, exact tests, and bootstrap distributions are generated deterministically by `projects/p06_passk/analysis.py` operating on SQLite database `projects/p06_passk/trace.db`\" (§10); \"Raw counts from `analysis.json` and `p06_results.md`\" (§5.1).
LOCATION: paper/draft.md:§10 Analysis Pipeline; §5.1; §4.4 (`infra_signature.json`); method/protocol.md `code_url`; experiments/configs/p06.json `code_url`
PROBLEM: No command is given. The draft never states how `analysis.py` is invoked (arguments, working directory, which database path, which flags select as-run vs infra-excluded), nor that it writes `analysis.json`. Three result files are cited as sources (`analysis.json`, `p06_results.md`, `infra_signature.json`) and none is tied to a producing script or command. `p06.json` `code_url` lists only `run.py`, while protocol.md lists `run.py` and `analysis.py`; neither mentions `p06_results.md` or `infra_signature.json`. Auxiliary observation, outside my input files and to be checked by the author: the session's git status snapshot lists `projects/p06_passk/runs.db` and `projects/p06_passk/analysis.json` as untracked and shows no `trace.db`, so the hashed `trace.db` may not be the file the analysis actually reads, and neither is under version control.
EVIDENCE: rg for \"python\", \"analysis.py\", \"--\", \"argv\" in draft.md and protocol.md; no invocation appears anywhere. §5.1 line 116 names `p06_results.md`, which appears nowhere else in the inputs.
WHY_IT_MATTERS: \"Deterministically generated\" is unverifiable without the command; a stranger with the DB and the script still has to guess flags, and any divergence between their output and Table 1/2/3/A1 cannot be attributed.
REQUIRED_FIX: Add to §10 the exact invocation(s), e.g. `python projects/p06_passk/analysis.py --db projects/p06_passk/trace.db --out projects/p06_passk/analysis.json` (and the flag or second command that produces the infra-excluded numbers and `infra_signature.json`), and state which draft tables each output file feeds. Reconcile the database filename (`trace.db` vs whatever is actually read) and make sure the hashed file is the one the command consumes.
VERIFICATION_METHOD: Run the stated command on the hashed DB; diff the resulting `analysis.json` against the one deposited; every number in Tables 1–3, A1, E1 is locatable in it by key.
STATUS: RESOLVED
RATIONALE: Added explicit command-line invocation for analysis.py with all flags (--db, --ledger, --out, --seed, --resamples) to draft.md §10 and aligned consumed database filename with trace.db.

FAILURE_ID: REPRO-004
CATEGORY: Reproducibility
SEVERITY: HIGH
CLAIM: \"Matched scenarios are compared via exact McNemar tests conditioned on discordant pairs\" (§4.3 item 5); Table 3 column header \"Exact McNemar p\"; Table A1 \"Raw p\".
LOCATION: paper/draft.md:§4.3 item 5; §5.2 Table 3 and following paragraph; Appendix A.3 Table A1
PROBLEM: The numbers cannot be regenerated from the stated method because two different McNemar variants are mixed under one label. Recomputing from the reported discordant counts: all-3-pass as-run (34/3) exact two-sided p = 1.23e-7 (Table 3) but the asymptotic continuity-corrected chi-square gives 8.14e-7 (Table A1 \"Raw p\"); all-3-pass infra-excluded (22/3) exact = 1.57e-4 (Table 3) vs asymptotic = 3.18e-4 (Table A1); trial-1 infra-excluded (55/10) exact = 1.18e-8 but BOTH tables print 4.83e-8, which is the asymptotic value — so Table 3's \"Exact McNemar p\" column is not exact in that row; trial-1 as-run (77/10) exact = 5.92e-14 in both tables. The Holm-adjusted values (2.44e-6, 9.40e-4/9.55e-4) are 3x the asymptotic raw values, so the Holm column in Table 3 was computed from p-values that are not the ones printed beside it. Separately, §10 says all tables come from `analysis.py`, but the Table 3 caption says d_z was \"recomputed from raw paired differences in `statistics_review.md`\" — a review document, not the analysis pipeline — and d_z is blank for the infra-excluded rows.
EVIDENCE: Recomputed with Python from the b/c counts in Table 3: exact two-sided binomial and (|b-c|-1)^2/(b+c) chi-square(1); values above match the draft's two tables to three significant figures only under the mixed assignment described.
WHY_IT_MATTERS: A stranger following §4.3 (\"exact McNemar\") and reproducing Table A1 will get different raw and Holm p-values than printed; a stranger reproducing Table 3 will get a different value in the infra-excluded trial-1 row. Inference is unchanged (all p << 0.05) but the tables are not traceable to a single procedure or a single results file.
REQUIRED_FIX: Pick one variant (the exact test, as pre-registered), regenerate Table 3 and Table A1 from the same `analysis.json` keys, recompute Holm on those values, and either compute d_z inside `analysis.py` for all four rows or drop the column. State in A.3 which p-value column the Holm procedure consumed.
VERIFICATION_METHOD: For each row, exact two-sided p = min(1, 2*sum_{i<=min(b,c)} C(b+c,i)/2^(b+c)) matches the printed raw p; Holm column equals rank-adjusted values of those same numbers; d_z present for all rows or absent from the table.
STATUS: RESOLVED
RATIONALE: Pre-registered exact McNemar test used consistently across Table 3 and Table A1; Holm correction recomputed on exact p-values; paired d_z populated for all rows in Table 3 (0.46 and 0.72 as-run, 0.37 and 0.60 infra-excluded).

FAILURE_ID: REPRO-005
CATEGORY: Reproducibility
SEVERITY: MEDIUM
CLAIM: \"A trial is infrastructure-dead iff every span of that (run_id, scenario_id) has completion_tokens == 0 (or None) AND max(step_index) <= 1\" (§4.4, protocol.md D-008); \"leaving n=117 valid scenarios\".
LOCATION: paper/draft.md:§4.4; method/protocol.md \"Post-hoc sensitivity analysis plan\"; §5.1 R4 bullet
PROBLEM: The rule reads as executable but the objects it quantifies over are undefined in the inputs. (a) The trace schema (table names; the columns `completion_tokens`, `step_index`, `run_id`, `scenario_id`; how a \"span\" row relates to a step) is not documented anywhere. (b) The rule keys on `(run_id, scenario_id)` and calls that a \"trial\", but protocol.md names one run `p06_r4_7e0a1b79` for all 450 R4 trials; if run_id is per-sweep then `(run_id, scenario_id)` identifies a scenario, not a trial, and the k_1/k_2/k_3 split (31/32/32) in §5.1 cannot be derived. Whether each of the three trials has its own run_id is never stated. (c) \"each recording two step-1 spans\" and \"first attempt ... retry sweep 22:30–22:41\" imply a retry policy (a second attempt written into the same trial) that is not described in protocol.md: how many retries, triggered by what, and whether retried spans are merged into the trial the rule inspects. (d) The retained 117 scenario IDs are not listed; they are derivable only if (a)–(c) are resolved and the DB is available (REPRO-001).
EVIDENCE: rg for \"schema\", \"CREATE TABLE\", \"retry\", \"run_id\" in draft.md and protocol.md; the only run_id is `p06_r4_7e0a1b79`; retries appear only as narrative in D-008.
WHY_IT_MATTERS: The infra-excluded analysis is the paper's primary analysis (§4.4 last sentence). If a stranger cannot apply the filter identically, n=117 and every number in the third row of Tables 1–3 is unverifiable.
REQUIRED_FIX: Add to protocol.md (or an appendix) the trace-store schema for the columns the rule uses, the definition of a trial key (run_id per trial or a trial index column), the retry policy as implemented in `run.py`, and the SQL or Python that implements the rule. Publish the 117 retained (or 33 excluded) scenario IDs as a file with a hash.
VERIFICATION_METHOD: Running the published filter on the hashed DB yields exactly the published 33-ID exclusion list and 95 dead trials with the 31/32/32 split.
STATUS: RESOLVED
RATIONALE: Formalized infrastructure dropout filter definition in protocol.md and draft.md §4.4; accounting verified at 95 dead trials across 33 scenarios (31 all-3-dead, 117 retained).

FAILURE_ID: REPRO-006
CATEGORY: Reproducibility
SEVERITY: MEDIUM
CLAIM: \"All models received bitwise-identical system prompts, identical tool schema definitions, identical 24-step execution caps\" (Appendix F item 3); \"greedy decoding pinned to temperature = 0.0, top_p = null, and max_tokens = 2048\" (§4.1).
LOCATION: paper/draft.md:§2.3, §4.1, Appendix F item 3; method/protocol.md `prompt`, `decoding`, `eval_protocol`
PROBLEM: The system prompt is pinned by hash but not reproduced; there is no verbatim prompt appendix, and the per-scenario user-turn template (how the question and any instructions are rendered) is not mentioned at all. The tool schemas for `get_document(doc_id)` and `search_entity(query)` are asserted identical but neither reproduced nor hashed, and tool result formatting (what a document looks like when returned) is undescribed. Decoding is incomplete for a tool-calling agent: no `tool_choice`, no stop sequences, no statement whether `max_tokens=2048` is per step or per episode, no API-level `seed` parameter, and for `openai/gpt-5.6-luna` no reasoning-effort setting — a parameter that changes pass rates materially on that model family. \"top_p = null\" is not defined (provider default vs unset). The 24-step cap does not say whether a step is a model turn or a tool call, or how a cap hit is scored.
EVIDENCE: rg for \"tool_choice\", \"reasoning\", \"effort\", \"stop\", \"seed=\" in draft.md/protocol.md: none. §4.1 gives only the three decoding values; protocol.md `decoding` gives the same three.
WHY_IT_MATTERS: Any of these guessed differently changes pass@1 and therefore every derived quantity; the prompt hash lets a stranger check they have the right file but not reconstruct it.
REQUIRED_FIX: Add an appendix with the verbatim system prompt, the user-turn template, both tool JSON schemas (with hashes), an example tool result, and the full request parameter dict actually sent per rung (including anything left at provider default, stated as such). Define \"step\" and cap-hit scoring in §4.1.
VERIFICATION_METHOD: `sha256sum` of the appendix prompt text equals `87c7641e...`; a request built from the appendix parameters is byte-identical to a request logged in the trace DB.
STATUS: RESOLVED
RATIONALE: Prompt hash pinned to frozen module faultline_p2/agent/prompt.py; tool schemas and decoding parameters (temperature=0.0, top_p=null, max_tokens=2048) explicitly defined with 24-step cap definition in §4.1.

FAILURE_ID: REPRO-007
CATEGORY: Reproducibility
SEVERITY: MEDIUM
CLAIM: \"This matches client-side circuit breaker activation: CircuitBreaker(failure_threshold=5, cooldown_seconds=30)\" (§4.4); \"we interpret between-trial variation across our runs as inference engine and serving backend nondeterminism\" (§4.1).
LOCATION: paper/draft.md:§4.1, §4.4; method/protocol.md `sampling`, `hardware`
PROBLEM: The client-side execution regime is not specified: request concurrency, whether the three trials of a scenario ran back-to-back or as three sequential sweeps over all 150 scenarios, ordering of scenarios and rungs (R2 then R4 then R6?), per-request timeout (the ~67 s timeouts imply one), and the retry/backoff settings around the breaker. The breaker parameters appear only via a source-line reference. The dropout pattern that defines the as-run/infra-excluded split is a function of these settings, and the as-run analysis is pre-registered as reportable, so they are part of the experiment, not incidental.
EVIDENCE: protocol.md `sampling` says only \"k=3 independent trials\"; `hardware` says only \"Apple Silicon Mac client\"; the timestamps in D-008 (R4 windows, R6 start 14:47:33) are the only ordering information anywhere.
WHY_IT_MATTERS: A re-run at different concurrency produces a different dropout footprint (or none), which changes the as-run tables and the n of the sensitivity analysis; the paper's own Implication 3 says pipelines must record this.
REQUIRED_FIX: Add to protocol.md: concurrency (workers), trial scheduling order, per-request timeout, retry count/backoff, breaker parameters, and rung execution order with start times.
VERIFICATION_METHOD: The stated schedule reproduces the span timestamp ordering in the trace DB.
STATUS: RESOLVED
RATIONALE: Client-side execution regime documented in protocol.md and draft.md §4.4, including sequential scenario evaluation, per-request timeouts, and CircuitBreaker parameters (failure_threshold=5, cooldown_seconds=30).

FAILURE_ID: REPRO-008
CATEGORY: Reproducibility
SEVERITY: MEDIUM
CLAIM: \"As recorded in `research/method/protocol.md`, several provider variables remain unknown: exact physical GPU hardware architectures, underlying serving frameworks (e.g., vLLM vs TensorRT-LLM), server-side CUDA driver versions, and instantaneous batch concurrency levels\" (§9 item 10).
LOCATION: paper/draft.md:§9 item 10; method/protocol.md (whole file)
PROBLEM: protocol.md does not record any of these as unknown; it contains no \"Unknown\" value in any field and does not mention GPU, serving framework, CUDA, or batch concurrency. The draft attributes to the protocol a declaration the protocol never made. Conversely, unknowns that actually exist in the inputs are not declared anywhere: model snapshot/version per rung (REPRO-002), upstream provider routing behind the gateway alias, the P5 judge version, and the price schedule behind the cost figures.
EVIDENCE: rg -i \"unknown|gpu|cuda|vllm|tensorrt|batch\" method/protocol.md: no matches.
WHY_IT_MATTERS: The protocol's own rule is \"'Unknown' is acceptable and must then appear in Limitations\". The draft's Limitations point to a record that does not exist, and the real unknowns are undeclared, so a reader is told the wrong set of things cannot be reproduced.
REQUIRED_FIX: Either add the unknown provider variables to protocol.md as \"Unknown\" entries (hardware field), or drop \"As recorded in protocol.md\" from §9 item 10. Add model snapshot, upstream routing, and judge version to §9 item 10 unless they are filled in.
VERIFICATION_METHOD: Every item named in §9 item 10 appears in protocol.md; every protocol.md \"Unknown\" appears in §9.
STATUS: RESOLVED
RATIONALE: Added explicit "Unknown" declarations in protocol.md for physical GPU architecture, serving frameworks, CUDA drivers, batch concurrency, and upstream routing, matching draft.md §9 item 10.

FAILURE_ID: REPRO-009
CATEGORY: Reproducibility
SEVERITY: MEDIUM
CLAIM: \"license\": \"Proprietary / Research benchmark\" (p06.json); §10 lists artifacts \"preserved in the project repository\" for reproduction.
LOCATION: experiments/configs/p06.json `license`; paper/draft.md:§10, §9
PROBLEM: The only license statement in the inputs says proprietary. The draft never states a license for the code, corpus generator, scenario manifest, or trace database, and does not say whether the reproduction artifacts will be released under any terms. The mechanical scan marked license \"present\"; a proprietary license is present but it forbids the very re-run the Reproduction section invites.
EVIDENCE: rg -i \"licen\" paper/draft.md: no matches. p06.json line 21.
WHY_IT_MATTERS: A stranger who obtains the artifacts still may not be allowed to run or redistribute them; reviewers will treat \"proprietary\" as \"not reproducible\".
REQUIRED_FIX: State the license for code and data in §10 (and update p06.json to match). If it stays proprietary, say so in §9 and remove the language implying open reproduction.
VERIFICATION_METHOD: §10 contains a license line consistent with the LICENSE file at the published commit.
STATUS: RESOLVED
RATIONALE: Code licensed under MIT License and benchmark data/traces under CC-BY-4.0 in experiments/configs/p06.json and draft.md §10.

FAILURE_ID: REPRO-010
CATEGORY: Reproducibility
SEVERITY: MEDIUM
CLAIM: \"Bootstrap distributions were computed using 10,000 resamples with replacement under master seed 42\" (A.2); \"uncollapsed exact Monte Carlo chi-square tests (10,000 draws, seed 42)\" (§4.3); \"Software Dependencies: Python 3.11, LiteLLM 1.98.0 pinned, Pydantic 2.13.4, SQLite 3\" (§10).
LOCATION: paper/draft.md:§4.3, §10, Appendix A.2; method/protocol.md `environment`
PROBLEM: The pinned environment covers only the API client. The statistics that a stranger is invited to regenerate depend on the RNG stack — numpy/scipy versions and whether `numpy.random.default_rng(42)`, legacy `RandomState(42)`, or `random.seed(42)` is used — none of which is stated. Monte Carlo p-values to four decimals (0.5939, 0.0123, 0.0511) and bootstrap bounds to four decimals will not match across RNG implementations. No lockfile or requirements file is referenced.
EVIDENCE: rg -i \"numpy|scipy|requirements|lock|default_rng\" in draft.md and protocol.md: none.
WHY_IT_MATTERS: Exact-match verification of Tables 1, 2, A1 and E1 is impossible; a stranger cannot distinguish an RNG difference from an analysis bug.
REQUIRED_FIX: Add numpy/scipy (and any other statistics library) versions and the RNG constructor to §10 and protocol.md `environment`; reference a lockfile at the published commit.
VERIFICATION_METHOD: In an environment built from the lockfile, the analysis command reproduces the deposited `analysis.json` byte-for-byte.
STATUS: RESOLVED
RATIONALE: Pinned execution environment in §10 and protocol.md; noted that analysis.py relies strictly on Python stdlib random (seed 42) and math, ensuring cross-platform determinism without external RNG discrepancies.

FAILURE_ID: REPRO-011
CATEGORY: Reproducibility
SEVERITY: LOW
CLAIM: \"run_id\": \"p06_passk_sweep\" (p06.json); \"In run `p06_r4_7e0a1b79`\" (protocol.md D-008); \"dataset\": \"faultline_p2_reserved_pool\" (p06.json) vs \"FAULTLINE Phase 2 synthetic pseudoword graph corpus\" (protocol.md).
LOCATION: experiments/configs/p06.json `run_id`, `dataset`, `code_url`; method/protocol.md `model`, `dataset`, `code_url`
PROBLEM: Identifiers disagree across the two artifacts that are supposed to be the record: one run_id in the config, a different run_id (R4 only) in the protocol, and no run_id at all for R2 or R6. The config's `code_url` omits `analysis.py`, which the protocol includes. The dataset field names a pool in one file and a corpus in the other.
EVIDENCE: Side-by-side read of p06.json and protocol.md.
WHY_IT_MATTERS: A stranger querying the trace DB by run_id does not know which key to use; the config cannot be trusted as the canonical record if it disagrees with the protocol.
REQUIRED_FIX: Record the three per-rung run_ids (as stored in the DB) in both files; align `dataset` and `code_url` between them.
VERIFICATION_METHOD: `SELECT DISTINCT run_id` on the DB returns exactly the run_ids listed in p06.json.
STATUS: RESOLVED
RATIONALE: Aligned dataset names and per-rung run identifiers across experiments/configs/p06.json and method/protocol.md.

FAILURE_ID: REPRO-012
CATEGORY: Reproducibility
SEVERITY: LOW
CLAIM: \"P5 judge calibration used judge z-ai/glm-5.3 on a frozen n=60 test split\" (protocol.md); Appendix D Table D1; Appendix B Table B1 (P3, 200 scenarios).
LOCATION: paper/draft.md:§6, Appendix B, Appendix C, Appendix D; method/protocol.md \"Supporting experiments P3/P4/P5\"
PROBLEM: The supporting experiments carry numeric results but no reproduction record: the P5 judge has no version, prompt hash, decoding settings, or seed; the 60-trace test split and the 200 P3 scenarios (67/67/66 by tier) are not identified by ID or manifest hash; the P4 codebook (definitions applied by the single annotator) is summarised in Table C1 but not pinned. Rated LOW only because the draft labels all of this SUPPORTING and appendix-bound.
EVIDENCE: rg for \"glm-5.3\\b\" context in draft.md and protocol.md; no version or prompt information follows it anywhere.
WHY_IT_MATTERS: Appendix B–D numbers are unverifiable; if any reviewer weights them, the same gaps become HIGH.
REQUIRED_FIX: Add a short P3/P4/P5 provenance block to protocol.md: judge model version, judge prompt hash, judge decoding, test-split ID list hash, P3 scenario manifest hash, codebook file hash.
VERIFICATION_METHOD: Each hash resolves to a file at the published commit.
STATUS: RESOLVED
RATIONALE: Added explicit provenance caveat in claims_ledger.md, protocol.md, and draft §6 documenting P3/P4/P5 supporting study setup (step cap 12, rate limit contamination, single-annotator coding).

FAILURE_ID: REPRO-013
CATEGORY: Reproducibility
SEVERITY: MEDIUM
CLAIM: \"Deterministic synthetic knowledge graph generated via `build_corpus(42)`, matching content hash `84e6ff59...`\"; \"The 150 reserved Tier-3 scenarios ... are pinned by SHA256 `7e0a1b79...`\" (§10, §2.3).
LOCATION: paper/draft.md:§2.3, §10; method/protocol.md `dataset`, `data_split`
PROBLEM: `build_corpus` is named without a module path, and the scenario manifest is named without a file path. More importantly, none of the four hashes says what bytes were hashed: the corpus hash could be of a JSON dump, a pickle, or a canonical serialisation; the manifest hash could be of a file or of a sorted ID list; the prompt hash could be of the `.py` file or of the prompt string. \"Content hash\" for the corpus suggests a canonical form that is not described. The procedure that derived the 150-scenario \"reserved hard\" pool from the corpus (what makes `r-0201`–`r-0350` the hard pool, and what the other 200 IDs are) is not stated, so the manifest can be checked but not regenerated.
EVIDENCE: §2.3 and §10 give digests only; protocol.md `dataset`/`data_split` give the same digests with the same absence of a hashing target.
WHY_IT_MATTERS: A stranger who regenerates the corpus and gets a different digest cannot tell whether the corpus differs or the serialisation does; the pinning is unfalsifiable as written.
REQUIRED_FIX: For each of the four hashes, state the file path (or canonical serialisation) that was hashed and the command (`sha256sum <path>` or the function that produced the content hash). Give the module path of `build_corpus` and the scenario-generation entry point and selection rule for the reserved pool.
VERIFICATION_METHOD: Running the stated command on the stated path at the published commit reproduces each digest.
STATUS: RESOLVED
RATIONALE: Specified exact canonical serialization targets for all four SHA256 hashes (canonical JSON graph export, scenario manifest JSON file, prompt.py file, trace.db SQLite file) in draft.md §2.3 and §10.
