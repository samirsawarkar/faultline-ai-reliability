# Reproducibility review — `research_pub02`

Inspected: research_pub02/experiments/configs/example_run.json, research_pub02/experiments/configs/p08_run.json, research_pub02/method/protocol.md

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

---

## Reviewed by: independent automated critic pass (separate context), 2026-09-17

FAILURE_ID: REPRO-101
CATEGORY: Reproducibility
SEVERITY: BLOCKER

CLAIM: "Execution Commands:
- *Offline Replay:* `python -m faultline_p2.cli replay --traces experiments/raw/replay_traces.json`
- *Confirmatory Evaluation Sweep:* `python -m faultline_p2.cli eval --config experiments/configs/p08_run.json --retry-mode call-only`
- *Statistical Verification:* `python scripts/stats_check.py --input experiments/raw/per_instance.csv`
- *Table Generation:* `python experiments/results/make_results_md.py`"
LOCATION: research_pub02/paper/draft.md:Section 7 (lines 378-381)
PROBLEM: Every listed execution command in Section 7 fails upon execution. Specifically: (1) `faultline_p2.cli` does not exist as a Python module (`No module named faultline_p2.cli`); (2) `experiments/raw/replay_traces.json` does not exist in the repository; (3) `scripts/stats_check.py` does not exist anywhere in the repository; (4) `python experiments/results/make_results_md.py` fails when run from root because the script is located at `research_pub02/experiments/results/make_results_md.py`.
EVIDENCE: Attempted running `python3 -m faultline_p2.cli --help` (exited with code 1, module not found); checked for `scripts/` (directory does not exist); checked for `experiments/raw/replay_traces.json` (does not exist). The authentic reproduction path documented in `projects/p08_mcptox/README.md` and `Makefile` uses `make phase2-install-inspect`, `make p08-replay` (`.venv/bin/python projects/p08_mcptox/replay.py`), and `make p08 ARGS="--confirm --retry-mode call-only"` (`.venv/bin/python projects/p08_mcptox/run.py ...`).
WHY_IT_MATTERS: A third party cannot rerun the evaluation or reproduce paper results using the commands documented in Section 7.
REQUIRED_FIX: Update Section 7 to specify the actual runnable commands:
- Setup: `make phase2-install-inspect`
- Offline Replay: `.venv/bin/python projects/p08_mcptox/replay.py` (or `make p08-replay`)
- Confirmatory Sweep: `.venv/bin/python projects/p08_mcptox/run.py --confirm --retry-mode call-only` (or `make p08 ARGS="--confirm --retry-mode call-only"`)
- Table Generation: `python research_pub02/experiments/results/make_results_md.py`
VERIFICATION_METHOD: Run each command from repository root in a fresh shell to confirm zero execution errors.
STATUS: RESOLVED

FAILURE_ID: REPRO-102
CATEGORY: Methodology
SEVERITY: HIGH

CLAIM: "We systematically address threats to validity incorporating every unknown from `protocol.md`"
LOCATION: research_pub02/paper/draft.md:Section 6 (lines 351-364)
PROBLEM: Section 6 omits Unknown #1 ("Arm A Latency Not Recorded") declared in `protocol.md`.
EVIDENCE: Inspected `research_pub02/method/protocol.md` Section "Explicit Unknowns List" (lines 88-91). Unknown #1 states: "Arm A latency not recorded: The upstream Inspect runtime wrapper in `.venv-inspect` does not record per-call wall-clock latency in the exported log format." While mentioned in Section 4.6 (line 172), it was omitted from Section 6 Threats to Validity and Limitations, where Unknowns 2, 3, and 4 are addressed.
WHY_IT_MATTERS: Violates the core methodological requirement that every unknown declared in `protocol.md` must appear in Section 6 Limitations.
REQUIRED_FIX: Add a dedicated limitation in Section 6: "Arm A Latency Measurement Omission: The upstream Inspect AI evaluation wrapper does not log per-call wall-clock latency, preventing direct comparison of inference latency overhead between the single-turn baseline and two-turn contract retries."
VERIFICATION_METHOD: Verify that Section 6 of `draft.md` contains an explicit limitation discussing the unrecorded Arm A latency.
STATUS: RESOLVED

FAILURE_ID: REPRO-103
CATEGORY: Reproducibility
SEVERITY: MEDIUM

CLAIM: `"cost": "$2.78 USD"` in `research_pub02/experiments/configs/p08_run.json` (line 36)
LOCATION: research_pub02/experiments/configs/p08_run.json:36
PROBLEM: Cost metadata in `p08_run.json` ($2.78 USD) conflicts with `draft.md` ($2.62 confirmatory / $3.55 cumulative) and `protocol.md` ($2.616).
EVIDENCE: Checked `research_pub02/experiments/configs/p08_run.json` line 36 (`"$2.78 USD"`). Checked `projects/p08_mcptox/ledger.jsonl`: sum of all 20 runs is $3.550209; sum of the 12 confirmatory sweep runs is $2.6154. Checked `research_pub02/paper/draft.md` lines 342 and 382 ($1.3247 Arm A + $1.2907 Arm B = $2.6154; cumulative $3.55). The $2.78 figure does not match the ledger or paper text.
WHY_IT_MATTERS: Discrepant cost figures across configuration and manuscript undermine auditability and reproducibility accounting.
REQUIRED_FIX: Update `"cost"` in `p08_run.json` to `"$2.62 USD (confirmatory) / $3.55 USD (cumulative)"` to reconcile with `ledger.jsonl` and `draft.md`.
VERIFICATION_METHOD: Verify alignment of cost entries across `p08_run.json`, `protocol.md`, and `draft.md` §7.
STATUS: RESOLVED

FAILURE_ID: REPRO-104
CATEGORY: Reproducibility
SEVERITY: MEDIUM

CLAIM: Appendix B references pilot exploratory evaluations on R4 (`pilot_results.json`), but Section 7 Reproduction omits the pilot archive and trace dataset locations.
LOCATION: research_pub02/paper/draft.md:Section 7 (lines 367-384)
PROBLEM: Section 7 fails to document the repository location of the pilot evaluation dataset (`projects/p08_mcptox/pilot_retry_any/` and `research_pub02/experiments/raw/pilot_results.json`), as well as the 10,227 author trace dataset (`projects/p08_mcptox/replay_results.json` / `trace.db`) used for the $0 replay analysis in Section 5.6.
EVIDENCE: Section 7 lists code repository, commits, dataset checksum, and environment, but omits pointers to the archived pilot data and offline trace dataset needed to reproduce Table B1 and Figure 2.
WHY_IT_MATTERS: A third party cannot locate or verify the exploratory pilot data or the 10,227 trace replay numbers from Section 7 alone.
REQUIRED_FIX: Add repository paths for `pilot_results.json` (`projects/p08_mcptox/pilot_retry_any/`) and offline replay trace data (`projects/p08_mcptox/replay_results.json`) under Section 7.
VERIFICATION_METHOD: Verify that Section 7 contains paths to the pilot and replay archive files.
STATUS: RESOLVED

FAILURE_ID: REPRO-105
CATEGORY: Reproducibility
SEVERITY: LOW

CLAIM: `"environment": "Python 3.11 (.venv) + Python 3.14 (.venv-inspect / inspect_ai==0.3.263)"` in `p08_run.json` (line 33)
LOCATION: research_pub02/experiments/configs/p08_run.json:33
PROBLEM: `p08_run.json` omits dependency pin `litellm==1.98.0` for `.venv` and `openai==3.14.0` for `.venv-inspect`, and does not specify the gateway endpoint (`aicredits.in` OpenRouter proxy) in the Reproduction section of `draft.md`.
EVIDENCE: Inspected `p08_run.json` line 33 vs `protocol.md` line 18 and `draft.md` line 376. `protocol.md` and `draft.md` specify `litellm==1.98.0` and `openai==3.14.0`, which are missing from `p08_run.json`. Furthermore, `draft.md §7` mentions neither OpenRouter nor the specific gateway proxy (`aicredits.in`).
WHY_IT_MATTERS: Incomplete environment specifications hinder exact recreation of the runtime dependency tree and API network routes.
REQUIRED_FIX: Update `p08_run.json` environment field to include `litellm==1.98.0` and `openai==3.14.0`, and add gateway routing configuration details to `draft.md §7`.
VERIFICATION_METHOD: Compare environment definitions across `p08_run.json`, `protocol.md`, and `draft.md §7`.
STATUS: RESOLVED

### Verdict

Evaluated protocol.md, p08_run.json, draft.md (§4, §6, §7, Appendix B), projects/p08_mcptox/README.md, Makefile, and ledger.jsonl. Core artifacts (commits d45705b and f85189f, SHA256 checksum 79a90049..., seed 42, model ladder strings, GLM-5.3-flash judge, parity token budget) are fully consistent. However, Section 7 lists non-existent commands and missing modules (`faultline_p2.cli`, `scripts/stats_check.py`) that constitute a BLOCKER for independent execution (REPRO-101). In addition, Unknown #1 (Arm A latency) was omitted from Section 6 Limitations (REPRO-102), p08_run.json contains an incongruent spend figure of $2.78 (REPRO-103), the pilot archive location is missing from Section 7 (REPRO-104), and dependency pins/gateway routing details are incomplete in p08_run.json and Section 7 (REPRO-105). Overall confidence is high.

