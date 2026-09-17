"""Statistical analysis for Project P6: Pass^k decay and scenario concentration.

Evaluates empirical pass^k decay vs naive compounding, intra-scenario correlation (ICC),
Fleiss' kappa, Binomial independence goodness-of-fit, and paired comparisons.
Pure standard library + faultline_p2.stats. Deterministic execution (seed=42).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sqlite3
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

from faultline_p2.stats.intervals import bootstrap, wilson_interval
from faultline_p2.stats.mathfns import binom_pmf, chi2_sf_df1
from faultline_p2.stats.paired import paired_table, mcnemar
from faultline_p2.stats.passk import naive_p_k, pass_hat_k

SEED = 42
N_RESAMPLES = 10_000


def chi2_survival_function(x: float, df: int) -> float:
    """Survival function P(X > x) for chi-square distribution with integer df >= 1.
    
    Formulas:
      df = 1: math.erfc(sqrt(x / 2))
      df = 2: exp(-x / 2)
      df = 3: erfc(sqrt(x / 2)) + sqrt(2 * x / pi) * exp(-x / 2)
      df = 2k (even): exp(-x / 2) * sum_{j=0}^{k-1} (x / 2)^j / j!
      df = 2k + 1 (odd): erfc(sqrt(x / 2)) + sqrt(2 * x / pi) * exp(-x / 2) * sum_{j=1}^k x^j / (2j - 1)!!
    """
    if x <= 0:
        return 1.0
    if df == 1:
        return chi2_sf_df1(x)
    elif df == 2:
        return math.exp(-x / 2.0)
    elif df == 3:
        return math.erfc(math.sqrt(x / 2.0)) + math.sqrt(2.0 * x / math.pi) * math.exp(-x / 2.0)
    elif df % 2 == 0:
        k = df // 2
        term = 1.0
        acc = 1.0
        for j in range(1, k):
            term *= (x / 2.0) / j
            acc += term
        return math.exp(-x / 2.0) * acc
    else:
        k = (df - 1) // 2
        term = 1.0
        acc = 0.0
        for j in range(1, k + 1):
            term *= x / (2 * j - 1)
            acc += term
        return math.erfc(math.sqrt(x / 2.0)) + math.sqrt(2.0 * x / math.pi) * math.exp(-x / 2.0) * (1.0 + acc)


def exact_binom_upper_tail(n: int, p: float, obs: int) -> float:
    """Exact upper tail P(X >= obs) for X ~ Binomial(n, p)."""
    if obs <= 0:
        return 1.0
    if obs > n:
        return 0.0
    if p <= 0.0:
        return 1.0 if obs == 0 else 0.0
    if p >= 1.0:
        return 1.0
    return sum(
        math.comb(n, j) * (p ** j) * ((1.0 - p) ** (n - j))
        for j in range(obs, n + 1)
    )


def load_scenario_trial_matrix(
    trace_db_path: Path,
    run_id: str,
) -> Tuple[Dict[str, List[bool]], int, int, int]:
    """Load scenario trial matrix from trace.db for a given run_id.
    
    Returns:
      (matrix_dict, spans_count, runs_count, max_verdicts_sum)
      where matrix_dict is {base_id: [bool, bool, bool]} ordered k1, k2, k3.
    """
    conn = sqlite3.connect(trace_db_path)
    try:
        spans_count = conn.execute(
            "SELECT count(*) FROM spans WHERE run_id = ?", (run_id,)
        ).fetchone()[0]
        
        rows = conn.execute(
            "SELECT scenario_id, max(verdict) FROM spans WHERE run_id = ? GROUP BY scenario_id",
            (run_id,),
        ).fetchall()
    finally:
        conn.close()

    runs_count = len(rows)
    max_verdicts_sum = sum(int(bool(v)) for _, v in rows)

    base_map: Dict[str, Dict[str, bool]] = {}
    for sid, v in rows:
        if "_" in sid:
            base, k = sid.rsplit("_", 1)
        else:
            base, k = sid, "k1"
        base_map.setdefault(base, {})[k] = bool(v)

    matrix: Dict[str, List[bool]] = {}
    for base in sorted(base_map.keys()):
        trials_dict = base_map[base]
        trial_keys = sorted(trials_dict.keys())
        matrix[base] = [trials_dict[k] for k in trial_keys]

    return matrix, spans_count, runs_count, max_verdicts_sum


def detect_infra_dead_trials(
    trace_db_path: Path,
    run_id: str,
) -> Dict[str, Any]:
    """Detect infrastructure-dead trials for a given run_id.
    
    A trial is infrastructure-dead iff every span of that (run_id, scenario_id)
    has completion_tokens == 0 (or None) AND max(step_index) <= 1.
    """
    conn = sqlite3.connect(trace_db_path)
    try:
        cursor = conn.execute(
            "SELECT scenario_id, step_index, completion_tokens, timestamp FROM spans WHERE run_id = ?",
            (run_id,),
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    spans_by_sid: Dict[str, List[Tuple[int, Optional[int], str]]] = {}
    for sid, step_idx, tokens, ts in rows:
        spans_by_sid.setdefault(sid, []).append((step_idx, tokens, ts))

    dead_trial_sids: Set[str] = set()
    dead_timestamps: List[str] = []

    for sid, spans in spans_by_sid.items():
        max_step = max(s[0] for s in spans)
        all_zero_tokens = all(s[1] is None or s[1] == 0 for s in spans)
        if max_step <= 1 and all_zero_tokens:
            dead_trial_sids.add(sid)
            for s in spans:
                dead_timestamps.append(s[2])

    dead_bases_map: Dict[str, Set[str]] = {}
    per_trial_split = {"k1": 0, "k2": 0, "k3": 0}
    for sid in dead_trial_sids:
        if "_" in sid:
            base, k = sid.rsplit("_", 1)
        else:
            base, k = sid, "k1"
        dead_bases_map.setdefault(base, set()).add(k)
        if k in per_trial_split:
            per_trial_split[k] += 1

    all3_bases = {base for base, trials in dead_bases_map.items() if len(trials) == 3}
    time_window = [min(dead_timestamps), max(dead_timestamps)] if dead_timestamps else None

    return {
        "dead_trial_scenario_ids": dead_trial_sids,
        "dead_base_scenarios": set(dead_bases_map.keys()),
        "all3_dead_base_scenarios": all3_bases,
        "per_trial_split": per_trial_split,
        "time_window": time_window,
        "infra_dead_trials": len(dead_trial_sids),
        "infra_dead_scenarios": len(dead_bases_map),
        "infra_dead_scenarios_all3": len(all3_bases),
    }


def segment_scenario_spans(
    spans_ordered_by_timestamp: List[Tuple[Any, ...]],
    step_index_pos: int = 1,
    timestamp_pos: int = 7,
) -> List[List[Tuple[Any, ...]]]:
    """Segment a time-ordered sequence of spans for one scenario into separate attempts.
    
    Per Decision D-010: a new attempt starts when step_index <= 1 and timestamp > previous span timestamp.
    The final attempt corresponds to the last contiguous span segment.
    """
    attempts: List[List[Tuple[Any, ...]]] = []
    for s in spans_ordered_by_timestamp:
        step_idx = s[step_index_pos]
        ts = s[timestamp_pos] if len(s) > timestamp_pos else ""
        if attempts and step_idx <= 1 and ts and ts > attempts[-1][-1][timestamp_pos]:
            attempts.append([s])
        elif not attempts:
            attempts.append([s])
        else:
            attempts[-1].append(s)
    return attempts


def classify_terminal_states(
    trace_db_path: Path,
    run_id: str,
) -> Dict[str, Any]:
    """Classify all runs for a given rung into mutually exclusive terminal states.
    
    Per Decision D-010: evaluates spans from the FINAL attempt (pass 2 at cap 24).
    Classification rules using the LATEST span at final-pass max step_index:
      1. 'answered_pass': max(verdict) == 1
      2. 'dead_at_start': max(step_index) <= 1 and completion_tokens == 0 on every span
      3. 'step_cap': max(step_index) >= 24
      4. 'midrun_no_completion': completion_tokens == 0 on terminal span, step_index > 1 and < 24
      5. 'step_cap_sub24': terminal span has termination_reason 'step_cap' with step_index < 24 (step 12 earlier cap)
      6. 'answered_fail': answer tool or termination_reason answered with verdict == 0
      7. 'other': any other termination reason
    """
    conn = sqlite3.connect(trace_db_path)
    try:
        cursor = conn.execute(
            """
            SELECT scenario_id, step_index, tool_name, completion_tokens, latency_ms, termination_reason, verdict, timestamp
            FROM spans
            WHERE run_id = ?
            ORDER BY scenario_id, timestamp ASC
            """,
            (run_id,),
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    spans_by_sid: Dict[str, List[Tuple[Any, ...]]] = {}
    for r in rows:
        spans_by_sid.setdefault(r[0], []).append(r)

    categories = [
        "answered_pass",
        "answered_fail",
        "step_cap",
        "step_cap_sub24",
        "dead_at_start",
        "midrun_no_completion",
        "other",
    ]
    summary: Dict[str, Dict[str, Any]] = {
        cat: {"total": 0, "k1": 0, "k2": 0, "k3": 0}
        for cat in categories
    }
    summary["dead_at_start"]["latency_signature"] = {"<1ms": 0, ">60s": 0, "other": 0}
    summary["midrun_no_completion"]["latency_signature"] = {"<1ms": 0, ">60s": 0, "other": 0}

    dead_at_start_scenarios: Set[str] = set()
    midrun_no_comp_scenarios: Set[str] = set()

    for sid, spans in spans_by_sid.items():
        base, k = sid.rsplit("_", 1) if "_" in sid else (sid, "k1")
        attempts = segment_scenario_spans(spans, step_index_pos=1, timestamp_pos=7)
        final_spans = attempts[-1]
        max_step = max(s[1] for s in final_spans)
        term_span = [s for s in final_spans if s[1] == max_step][-1]
        
        # fields: sid, step_index, tool_name, completion_tokens, latency_ms, termination_reason, verdict, timestamp
        term_tool = term_span[2]
        term_tokens = term_span[3]
        term_lat = term_span[4] or 0.0
        term_reason = term_span[5]
        max_verdict = max((s[6] for s in final_spans if s[6] is not None), default=0)
        all_zero_tokens = all(s[3] is None or s[3] == 0 for s in final_spans)

        if max_verdict == 1:
            cat = "answered_pass"
        elif max_step <= 1 and all_zero_tokens:
            cat = "dead_at_start"
            dead_at_start_scenarios.add(base)
            lat_cat = "<1ms" if term_lat < 1.0 else (">60s" if term_lat > 60000.0 else "other")
            summary["dead_at_start"]["latency_signature"][lat_cat] += 1
        elif max_step >= 24:
            cat = "step_cap"
        elif (term_tokens is None or term_tokens == 0) and 1 < max_step < 24:
            cat = "midrun_no_completion"
            midrun_no_comp_scenarios.add(base)
            lat_cat = "<1ms" if term_lat < 1.0 else (">60s" if term_lat > 60000.0 else "other")
            summary["midrun_no_completion"]["latency_signature"][lat_cat] += 1
        elif term_reason == "step_cap" and max_step < 24:
            cat = "step_cap_sub24"
        elif term_reason == "answered" or term_tool == "answer":
            cat = "answered_fail"
        else:
            cat = "other"

        summary[cat]["total"] += 1
        if k in summary[cat]:
            summary[cat][k] += 1

    strict_dropped = sorted(dead_at_start_scenarios | midrun_no_comp_scenarios)
    all_bases = sorted(list(set(sid.rsplit("_", 1)[0] if "_" in sid else sid for sid in spans_by_sid.keys())))
    strict_retained = [b for b in all_bases if b not in strict_dropped]

    return {
        "categories": summary,
        "dead_at_start_scenarios": sorted(dead_at_start_scenarios),
        "midrun_no_completion_scenarios": sorted(midrun_no_comp_scenarios),
        "strict_dropped_scenarios": strict_dropped,
        "strict_retained_scenarios": strict_retained,
        "method": (
            "Classification using latest span at final-pass max step_index per Decision D-010: "
            "answered_pass (verdict=1); dead_at_start (max_step<=1 and completion_tokens=0 on all spans); "
            "step_cap (max_step>=24); midrun_no_completion (completion_tokens=0 on terminal span, 1<max_step<24); "
            "step_cap_sub24 (terminal termination_reason 'step_cap' with max_step=12 from prior cap); "
            "answered_fail (answer tool / termination answered, verdict=0); other (all other termination reasons)."
        ),
    }


def compute_pass_at_1(
    scenario_matrix: List[List[bool]],
    seed: int = SEED,
    n_resamples: int = N_RESAMPLES,
) -> Dict[str, Any]:
    """Calculate pass@1 pooled over all trials, with Wilson and scenario bootstrap CIs."""
    n_scenarios = len(scenario_matrix)
    k_trials = len(scenario_matrix[0]) if n_scenarios > 0 else 0
    total_trials = n_scenarios * k_trials
    passing_trials = sum(sum(row) for row in scenario_matrix)
    
    score = passing_trials / total_trials if total_trials > 0 else 0.0
    w_ci = wilson_interval(passing_trials, total_trials, confidence=0.95)
    
    scenario_fractions = [sum(row) / float(len(row)) for row in scenario_matrix]
    boot_ci = bootstrap(
        scenario_fractions,
        statistic=lambda s: sum(s) / len(s) if s else 0.0,
        n_resamples=n_resamples,
        seed=seed,
    )
    
    return {
        "bootstrap_method": f"scenario_level_percentile_bootstrap_{n_resamples}_seed{seed}",
        "passing_trials": passing_trials,
        "scenario_bootstrap_ci": [round(boot_ci[0], 6), round(boot_ci[1], 6)],
        "score": round(score, 6),
        "total_trials": total_trials,
        "wilson_ci": [round(w_ci[0], 6), round(w_ci[1], 6)],
        "wilson_method": "wilson_score_interval_95pct",
    }


def compute_pass_k(
    scenario_matrix: List[List[bool]],
    k: int,
    seed: int = SEED,
    n_resamples: int = N_RESAMPLES,
) -> Dict[str, Any]:
    """Calculate empirical pass^k, naive (pass@1)^k, delta, and concentration ratio C_k with bootstrap CIs."""
    n_scenarios = len(scenario_matrix)
    total_trials = n_scenarios * len(scenario_matrix[0]) if n_scenarios > 0 else 0
    total_passes = sum(sum(row) for row in scenario_matrix)
    p1 = total_passes / float(total_trials) if total_trials > 0 else 0.0
    
    p_hat_k = pass_hat_k(scenario_matrix, k)
    naive = naive_p_k(p1, k)
    c_k = p_hat_k / naive if naive > 0 else 1.0
    delta = p_hat_k - naive

    p_hat_boot = bootstrap(
        scenario_matrix,
        statistic=lambda s: pass_hat_k(s, k),
        n_resamples=n_resamples,
        seed=seed,
    )
    
    naive_boot = bootstrap(
        scenario_matrix,
        statistic=lambda s: naive_p_k(sum(sum(r) for r in s) / (len(s) * len(s[0])), k),
        n_resamples=n_resamples,
        seed=seed,
    )

    def ratio_stat(s: Sequence[List[bool]]) -> float:
        n_tot = len(s) * len(s[0])
        p1_resamp = sum(sum(r) for r in s) / float(n_tot)
        denom = naive_p_k(p1_resamp, k)
        num = pass_hat_k(s, k)
        return num / denom if denom > 0 else 0.0

    ratio_boot = bootstrap(
        scenario_matrix,
        statistic=ratio_stat,
        n_resamples=n_resamples,
        seed=seed,
    )

    def delta_stat(s: Sequence[List[bool]]) -> float:
        n_tot = len(s) * len(s[0])
        p1_resamp = sum(sum(r) for r in s) / float(n_tot)
        return pass_hat_k(s, k) - naive_p_k(p1_resamp, k)

    delta_boot = bootstrap(
        scenario_matrix,
        statistic=delta_stat,
        n_resamples=n_resamples,
        seed=seed,
    )

    res: Dict[str, Any] = {
        "concentration_ratio_C_k": round(c_k, 6),
        "concentration_ratio_bootstrap_ci": [round(ratio_boot[0], 6), round(ratio_boot[1], 6)],
        "deviation_delta": round(delta, 6),
        "deviation_delta_bootstrap_ci": [round(delta_boot[0], 6), round(delta_boot[1], 6)],
        "deviation_delta_method": f"scenario_level_delta_bootstrap_{n_resamples}_seed{seed}",
        "k": k,
        "naive_k": round(naive, 6),
        "naive_k_bootstrap_ci": [round(naive_boot[0], 6), round(naive_boot[1], 6)],
        "naive_k_method": f"naive_p_k_pow_{k}",
        "pass_hat_k": round(p_hat_k, 6),
        "pass_hat_k_bootstrap_ci": [round(p_hat_boot[0], 6), round(p_hat_boot[1], 6)],
        "pass_hat_k_method": f"pass_hat_k_first_{k}_trials",
        "ratio_method": f"honest_scenario_level_ratio_bootstrap_{n_resamples}_seed{seed}",
    }

    if k == 2 and scenario_matrix and len(scenario_matrix[0]) == 3:
        def calc_all_pairs(mat: Sequence[List[bool]]) -> float:
            return sum(math.comb(sum(r), 2) / 3.0 for r in mat) / float(len(mat))

        p2_pairs = calc_all_pairs(scenario_matrix)
        pairs_boot = bootstrap(
            scenario_matrix,
            statistic=calc_all_pairs,
            n_resamples=n_resamples,
            seed=seed,
        )
        res["pass_2_all_pairs"] = round(p2_pairs, 6)
        res["pass_2_all_pairs_bootstrap_ci"] = [round(pairs_boot[0], 6), round(pairs_boot[1], 6)]
        res["pass_2_all_pairs_method"] = "subset_average_over_3_choose_2_pairs"

    return res


def compute_tarone_z_test(scenario_matrix: List[List[bool]]) -> Dict[str, Any]:
    """Tarone (1979) score test for binomial goodness-of-fit against beta-binomial overdispersion.
    
    Reference: Tarone, R. E. (1979). Testing the goodness of fit of the binomial distribution.
    Biometrika 66(3), 585-590.
    
    Test statistic:
      S = sum_{i=1}^N (x_i - n * p_hat)^2 / (n * p_hat * (1 - p_hat))
      z = (n * S - N * n) / sqrt(2 * N * n * (n - 1))
    where N is the number of clusters (scenarios) and n is trials per cluster.
    Under H0 (homogeneous binomial), z ~ N(0, 1) asymptotically.
    One-sided p-value for overdispersion (z > 0): 0.5 * erfc(z / sqrt(2)).
    """
    N = len(scenario_matrix)
    n = len(scenario_matrix[0]) if N > 0 else 0
    if N == 0 or n <= 1:
        return {
            "dispersion_statistic_S": 0.0,
            "method": "tarone_1979_c_alpha_score_test",
            "n_clusters": N,
            "p_hat": 0.0,
            "p_value": 1.0,
            "trials_per_cluster": n,
            "z_statistic": 0.0,
        }
    
    x_i = [sum(r) for r in scenario_matrix]
    X = sum(x_i)
    total_obs = N * n
    p_hat = X / float(total_obs)
    q_hat = 1.0 - p_hat
    
    if p_hat <= 0.0 or p_hat >= 1.0:
        return {
            "dispersion_statistic_S": 0.0,
            "method": "tarone_1979_c_alpha_score_test",
            "n_clusters": N,
            "p_hat": round(p_hat, 6),
            "p_value": 1.0,
            "trials_per_cluster": n,
            "z_statistic": 0.0,
        }
    
    S = sum((x - n * p_hat) ** 2 for x in x_i) / (n * p_hat * q_hat)
    denom = math.sqrt(2.0 * N * n * (n - 1))
    z = (n * S - N * n) / denom
    p_val = 0.5 * math.erfc(z / math.sqrt(2.0))
    
    return {
        "dispersion_statistic_S": round(S, 6),
        "method": "tarone_1979_c_alpha_score_test",
        "n_clusters": N,
        "p_hat": round(p_hat, 6),
        "p_value": round(p_val, 6),
        "trials_per_cluster": n,
        "z_statistic": round(z, 6),
    }


def compute_independence_test(
    scenario_matrix: List[List[bool]],
    seed: int = SEED,
    n_mc_draws: int = N_RESAMPLES,
) -> Dict[str, Any]:
    """Pearson chi-square goodness-of-fit with df=2 asymptotic reference and parametric bootstrap.
    
    Accounts for pass@1 being estimated from the same data:
      - Primary asymptotic df = 2 (4 cells - 1 - 1 fitted parameter).
      - Primary Monte Carlo p is a parametric bootstrap: for each draw, simulate n scenarios x 3 trials
        with Bernoulli(p_hat), re-estimate p_hat* from the draw, compute expected counts from p_hat*,
        and evaluate Pearson chi2 against expected counts.
      - Tarone (1979) C(alpha) score test against beta-binomial overdispersion.
      - Exact binomial upper-tail test on always-pass count, plus parametric bootstrap tail probability.
      - Legacy fixed-p Monte Carlo and collapsed test are preserved under 'legacy' keys.
    """
    n_scenarios = len(scenario_matrix)
    k_trials = len(scenario_matrix[0])
    counts: Dict[int, int] = {j: 0 for j in range(k_trials + 1)}
    total_passes = 0
    for row in scenario_matrix:
        s = sum(row)
        counts[s] += 1
        total_passes += s

    p = total_passes / float(n_scenarios * k_trials) if (n_scenarios * k_trials) > 0 else 0.0
    expected = {j: n_scenarios * binom_pmf(j, k_trials, p) for j in range(k_trials + 1)}

    # Uncollapsed Pearson chi-square statistic
    chi2_uncoll = sum(
        ((counts[j] - expected[j]) ** 2) / expected[j] if expected[j] > 0 else 0.0
        for j in range(k_trials + 1)
    )
    
    # Correct df = 4 cells - 1 - 1 parameter = 2
    df_correct = max(1, k_trials - 1)  # df = 2
    p_val_asymp_df2 = chi2_survival_function(chi2_uncoll, df_correct)

    # Legacy df = 3
    df_legacy = k_trials
    p_val_asymp_df3 = chi2_survival_function(chi2_uncoll, df_legacy)

    # Legacy collapsing algorithm for cells with expected < 5.0
    bins: List[List[int]] = [[j] for j in range(k_trials + 1)]
    collapsed_any = False
    
    while len(bins) > 1 and sum(expected[j] for j in bins[-1]) < 5.0:
        collapsed_any = True
        popped = bins.pop()
        bins[-1].extend(popped)
        
    while len(bins) > 1 and sum(expected[j] for j in bins[0]) < 5.0:
        collapsed_any = True
        popped = bins.pop(0)
        bins[0] = popped + bins[0]

    obs_coll = [sum(counts[j] for j in b) for b in bins]
    exp_coll = [sum(expected[j] for j in b) for b in bins]
    
    chi2_coll = sum(
        ((o - e) ** 2) / e if e > 0 else 0.0
        for o, e in zip(obs_coll, exp_coll)
    )
    df_coll = max(1, len(bins) - 1)
    p_val_coll = chi2_survival_function(chi2_coll, df_coll)

    # Simulation loop: parametric bootstrap (p* re-estimated) + legacy fixed-p
    rng = random.Random(seed)
    mc_param_greater = 0
    mc_fixed_greater = 0
    mc_coll_greater = 0
    mc_param_tail_greater = 0
    obs_always_pass = counts[k_trials]

    for _ in range(n_mc_draws):
        draw_counts = {j: 0 for j in range(k_trials + 1)}
        draw_total_passes = 0
        for _ in range(n_scenarios):
            s = sum(1 for _ in range(k_trials) if rng.random() < p)
            draw_counts[s] += 1
            draw_total_passes += s

        # 1. Parametric bootstrap: re-estimate p* from the draw
        p_star = draw_total_passes / float(n_scenarios * k_trials) if (n_scenarios * k_trials) > 0 else 0.0
        exp_star = {j: n_scenarios * binom_pmf(j, k_trials, p_star) for j in range(k_trials + 1)}
        stat_param = sum(
            ((draw_counts[j] - exp_star[j]) ** 2) / exp_star[j] if exp_star[j] > 0 else 0.0
            for j in range(k_trials + 1)
        )
        if stat_param >= chi2_uncoll:
            mc_param_greater += 1

        if draw_counts[k_trials] >= obs_always_pass:
            mc_param_tail_greater += 1

        # 2. Legacy fixed-p uncollapsed
        stat_fixed = sum(
            ((draw_counts[j] - expected[j]) ** 2) / expected[j] if expected[j] > 0 else 0.0
            for j in range(k_trials + 1)
        )
        if stat_fixed >= chi2_uncoll:
            mc_fixed_greater += 1

        # 3. Legacy fixed-p collapsed
        draw_obs_coll = [sum(draw_counts[j] for j in b) for b in bins]
        stat_co = sum(
            ((o - e) ** 2) / e if e > 0 else 0.0
            for o, e in zip(draw_obs_coll, exp_coll)
        )
        if stat_co >= chi2_coll:
            mc_coll_greater += 1

    param_bootstrap_p = mc_param_greater / float(n_mc_draws)
    legacy_mc_p_uncoll = mc_fixed_greater / float(n_mc_draws)
    legacy_mc_p_coll = mc_coll_greater / float(n_mc_draws)
    param_bootstrap_tail_p = mc_param_tail_greater / float(n_mc_draws)

    # Exact binomial tail on always-pass count
    exact_tail_p = exact_binom_upper_tail(n_scenarios, p ** k_trials, obs_always_pass)

    bin_labels = [
        str(b[0]) if len(b) == 1 else f"{{{','.join(map(str, b))}}}"
        for b in bins
    ]

    return {
        "binomial_p": round(p, 6),
        "chi2_df": df_correct,
        "chi2_p_value_asymptotic": round(p_val_asymp_df2, 6),
        "chi2_statistic": round(chi2_uncoll, 6),
        "expected_histogram": {j: round(expected[j], 4) for j in range(k_trials + 1)},
        "legacy": {
            "chi2_uncollapsed_fixed_p": {
                "df": df_legacy,
                "monte_carlo_p_value": round(legacy_mc_p_uncoll, 6),
                "p_value_asymptotic": round(p_val_asymp_df3, 6),
                "statistic": round(chi2_uncoll, 6),
            },
            "collapsing": {
                "bins": bin_labels,
                "cells_collapsed": collapsed_any,
                "chi2_df": df_coll,
                "chi2_p_value_asymptotic": round(p_val_coll, 6),
                "chi2_statistic": round(chi2_coll, 6),
                "expected": [round(e, 4) for e in exp_coll],
                "monte_carlo_p_value": round(legacy_mc_p_coll, 6),
                "observed": obs_coll,
                "reason": "Merged adjacent tail cells with expected count < 5.0" if collapsed_any else "No cells had expected count < 5.0",
            },
        },
        "method": "pearson_chi2_goodness_of_fit_df2_parametric_bootstrap_reestimating_p",
        "monte_carlo_method": f"parametric_bootstrap_{n_mc_draws}_draws_reestimating_p_seed{seed}",
        "monte_carlo_p_value": round(param_bootstrap_p, 6),
        "observed_histogram": counts,
        "parametric_bootstrap_p_value": round(param_bootstrap_p, 6),
        "tail_test": {
            "always_pass_expected": round(expected[k_trials], 4),
            "always_pass_observed": obs_always_pass,
            "exact_tail_p_value": round(exact_tail_p, 6),
            "method": "exact_binomial_upper_tail_and_parametric_bootstrap",
            "parametric_bootstrap_tail_p_value": round(param_bootstrap_tail_p, 6),
        },
        "tarone_z_test": compute_tarone_z_test(scenario_matrix),
    }


def compute_beta_binomial_extrapolation(
    scenario_matrix: List[List[bool]],
    icc: float,
    icc_ci: List[float],
    seed: int = SEED,
    n_resamples: int = N_RESAMPLES,
) -> Dict[str, Any]:
    """Extrapolate pass^k and concentration ratio C_k for k=1..10 under beta-binomial compounding model.
    
    Evaluates Reviewer #2 R2-003 concern: tests whether consistency with independence at k=3
    is compatible with substantial under-prediction of joint reliability at operational k (e.g. k=8).
    Closed-form beta-binomial moments:
      E[p^k] = prod_{i=0}^{k-1} (a + i) / (a + b + i)
      where a + b = (1 - rho) / rho, a = p1 * (a + b), b = (1 - p1) * (a + b).
    """
    n_scen = len(scenario_matrix)
    k_trials = len(scenario_matrix[0]) if n_scen > 0 else 0
    total_trials = n_scen * k_trials
    p1 = sum(sum(r) for r in scenario_matrix) / float(total_trials) if total_trials > 0 else 0.0

    def e_pk(m: float, rho: float, k: int) -> float:
        if rho <= 0.0 or m <= 0.0:
            return m ** k
        if m >= 1.0:
            return 1.0
        if rho >= 1.0:
            return m
        s = (1.0 - rho) / rho
        a = m * s
        b = (1.0 - m) * s
        if (a + b) <= 0.0:
            return m
        val = 1.0
        for i in range(k):
            denom = a + b + i
            val *= (a + i) / denom if denom > 0 else 1.0
        return val

    # Scenario bootstrap to estimate empirical percentile CIs on C_k
    rng = random.Random(seed)
    resample_ck: Dict[int, List[float]] = {k: [] for k in range(1, 11)}
    for _ in range(n_resamples):
        sample = [scenario_matrix[rng.randint(0, n_scen - 1)] for _ in range(n_scen)]
        p_s = sum(sum(r) for r in sample) / float(total_trials) if total_trials > 0 else 0.0
        if p_s <= 0.0 or p_s >= 1.0:
            for k in range(1, 11):
                resample_ck[k].append(1.0)
            continue
        # ANOVA ICC on sample
        s_means = [sum(r) / float(k_trials) for r in sample]
        grand_mean = sum(s_means) / float(n_scen)
        ssb = k_trials * sum((m_i - grand_mean) ** 2 for m_i in s_means)
        msb = ssb / float(n_scen - 1) if n_scen > 1 else 0.0
        ssw = sum(sum((x - m_i) ** 2 for x in r) for r, m_i in zip(sample, s_means))
        msw = ssw / float(n_scen * (k_trials - 1)) if n_scen * (k_trials - 1) > 0 else 0.0
        denom = msb + (k_trials - 1) * msw
        rho_s = (msb - msw) / denom if denom > 0 else 0.0
        
        for k in range(1, 11):
            num = e_pk(p_s, rho_s, k)
            denom_k = p_s ** k
            resample_ck[k].append(num / denom_k if denom_k > 0 else 1.0)

    table: Dict[str, Any] = {}
    for k in range(1, 11):
        pt_ck = e_pk(p1, icc, k) / (p1 ** k) if p1 > 0 else 1.0
        up_ck = e_pk(p1, icc_ci[1], k) / (p1 ** k) if p1 > 0 else 1.0
        vals = sorted(resample_ck[k])
        lo_idx = int(0.025 * len(vals))
        hi_idx = int(0.975 * len(vals))
        table[f"k{k}"] = {
            "concentration_ratio_C_k": round(pt_ck, 4),
            "concentration_ratio_at_icc_ci_upper": round(up_ck, 4),
            "concentration_ratio_bootstrap_ci": [round(vals[lo_idx], 4), round(vals[hi_idx], 4)],
            "expected_pass_k": round(e_pk(p1, icc, k), 6),
            "k": k,
            "naive_pass_k": round(p1 ** k, 6),
        }
    return table


def compute_intra_scenario_correlation(
    scenario_matrix: List[List[bool]],
    seed: int = SEED,
    n_resamples: int = N_RESAMPLES,
) -> Dict[str, Any]:
    """Intra-scenario correlation: one-way ANOVA ICC(1,1) and Fleiss' kappa for binary ratings."""
    n = len(scenario_matrix)
    k = len(scenario_matrix[0]) if n > 0 else 0

    def calc_icc(mat: Sequence[List[bool]]) -> float:
        n_scen = len(mat)
        if n_scen <= 1:
            return 0.0
        k_tr = len(mat[0])
        x_bar_i = [sum(r) / float(k_tr) for r in mat]
        x_bar = sum(sum(r) for r in mat) / float(n_scen * k_tr)
        
        ssb = k_tr * sum((xi - x_bar) ** 2 for xi in x_bar_i)
        msb = ssb / float(n_scen - 1)
        
        ssw = sum(sum((x - xi) ** 2 for x in r) for r, xi in zip(mat, x_bar_i))
        msw = ssw / float(n_scen * (k_tr - 1))
        
        denom = msb + (k_tr - 1) * msw
        return (msb - msw) / denom if denom > 0 else 0.0

    def calc_fleiss(mat: Sequence[List[bool]]) -> float:
        n_scen = len(mat)
        if n_scen == 0:
            return 0.0
        k_tr = len(mat[0])
        p_i_list = []
        for r in mat:
            n1 = sum(r)
            n0 = k_tr - n1
            p_agree = (n1 * (n1 - 1) + n0 * (n0 - 1)) / float(k_tr * (k_tr - 1))
            p_i_list.append(p_agree)
        p_bar = sum(p_i_list) / float(n_scen)
        p1 = sum(sum(r) for r in mat) / float(n_scen * k_tr)
        p0 = 1.0 - p1
        pe_bar = p0 ** 2 + p1 ** 2
        denom = 1.0 - pe_bar
        return (p_bar - pe_bar) / denom if denom > 0 else 0.0

    icc_val = calc_icc(scenario_matrix)
    icc_ci = bootstrap(scenario_matrix, statistic=calc_icc, n_resamples=n_resamples, seed=seed)

    fleiss_val = calc_fleiss(scenario_matrix)
    fleiss_ci = bootstrap(scenario_matrix, statistic=calc_fleiss, n_resamples=n_resamples, seed=seed)

    extrap_table = compute_beta_binomial_extrapolation(
        scenario_matrix, icc_val, [round(icc_ci[0], 6), round(icc_ci[1], 6)], seed=seed, n_resamples=n_resamples
    )

    return {
        "extrapolation_table_beta_binomial": extrap_table,
        "fleiss_kappa": round(fleiss_val, 6),
        "fleiss_kappa_bootstrap_ci": [round(fleiss_ci[0], 6), round(fleiss_ci[1], 6)],
        "fleiss_kappa_method": "fleiss_multirater_kappa",
        "icc": round(icc_val, 6),
        "icc_bootstrap_ci": [round(icc_ci[0], 6), round(icc_ci[1], 6)],
        "icc_method": "one_way_random_effects_anova_icc1_1",
    }


def compute_concentration_counts(scenario_matrix: List[List[bool]]) -> Dict[str, int]:
    """Plain-language concentration counts: always pass, always fail, mixed."""
    k = len(scenario_matrix[0]) if scenario_matrix else 0
    always_pass = 0
    always_fail = 0
    mixed = 0
    for row in scenario_matrix:
        s = sum(row)
        if s == k:
            always_pass += 1
        elif s == 0:
            always_fail += 1
        else:
            mixed += 1
    return {
        "always_fail": always_fail,
        "always_pass": always_pass,
        "mixed": mixed,
        "total_scenarios": len(scenario_matrix),
    }


def compute_cost_per_grounded_pass(
    scenario_matrix: List[List[bool]],
    ledger_path: Path,
    rung: str,
    seed: int = SEED,
    n_resamples: int = N_RESAMPLES,
) -> Dict[str, Any]:
    """Cost per grounded pass: final pass spend from ledger.jsonl / number of passing trials, with denominator bootstrap CI.
    
    Per Decision D-010: Pass 1 spend is discarded; Pass 2 spend (timestamp >= 2026-09-11T18:00:00)
    is the primary final-pass spend used for cost-efficiency.
    """
    total_spend = 0.0
    final_pass_spend = 0.0
    discarded_spend = 0.0
    if ledger_path.exists():
        with open(ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                if row.get("rung") == rung:
                    usd = float(row.get("usd", 0.0))
                    total_spend += usd
                    ts = row.get("timestamp_utc", "")
                    if ts >= "2026-09-11T18:00:00":
                        final_pass_spend += usd
                    else:
                        discarded_spend += usd

    active_spend = final_pass_spend if final_pass_spend > 0 else total_spend
    passing_trials = sum(sum(row) for row in scenario_matrix)
    cost_per_pass = active_spend / float(passing_trials) if passing_trials > 0 else 0.0

    denom_boot = bootstrap(
        scenario_matrix,
        statistic=lambda s: float(sum(sum(r) for r in s)),
        n_resamples=n_resamples,
        seed=seed,
    )
    
    cost_boot = bootstrap(
        scenario_matrix,
        statistic=lambda s: (active_spend / float(sum(sum(r) for r in s))) if sum(sum(r) for r in s) > 0 else 0.0,
        n_resamples=n_resamples,
        seed=seed,
    )

    return {
        "cost_per_grounded_pass_bootstrap_ci": [round(cost_boot[0], 6), round(cost_boot[1], 6)],
        "cost_per_grounded_pass_usd": round(cost_per_pass, 6),
        "discarded_spend_usd": round(discarded_spend, 6),
        "final_pass_spend_usd": round(final_pass_spend, 6),
        "method": "final_pass_ledger_spend_div_passing_trials_with_scenario_bootstrap",
        "passing_trials": passing_trials,
        "passing_trials_bootstrap_ci": [int(round(denom_boot[0])), int(round(denom_boot[1]))],
        "total_spend_usd": round(total_spend, 6),
    }


def compute_paired_comparison(
    r2_matrix: List[List[bool]],
    r4_matrix: List[List[bool]],
    seed: int = SEED,
    n_resamples: int = N_RESAMPLES,
) -> Dict[str, Any]:
    """Paired comparisons between R2 and R4 for all-3-pass and trial-1 pass.
    
    Reports exact p as primary, chi2 with continuity correction as secondary.
    Computes paired Cohen's d_z from identical 0/1 vectors (mean diff / sample SD ddof=1),
    scenario-bootstrap risk difference CI, and log-normal odds ratio CI.
    """
    def run_sub_comparison(r2_seq: List[bool], r4_seq: List[bool], mode_name: str) -> Dict[str, Any]:
        t = paired_table(r2_seq, r4_seq)
        mcn = mcnemar(t.a_only, t.b_only, correction=True)
        
        # Primary exact binomial p-value, secondary continuity-corrected chi2 p-value
        exact_p = mcn["exact_p_value"]
        chi2_p = mcn["chi2_p_value"]
        chi2_stat = mcn["chi2_statistic"]

        # Form paired difference vector (Y2 - Y4)
        diffs = [int(v2) - int(v4) for v2, v4 in zip(r2_seq, r4_seq)]
        n = len(diffs)
        mean_d = sum(diffs) / float(n) if n > 0 else 0.0
        if n > 1:
            var_d = sum((d - mean_d) ** 2 for d in diffs) / float(n - 1)
            sd_d = math.sqrt(var_d)
            dz = mean_d / sd_d if sd_d > 0 else 0.0
        else:
            sd_d = 0.0
            dz = 0.0

        ties_count = t.both_correct + t.both_wrong
        table_dict = t.to_dict()
        table_dict["ties"] = ties_count

        # Risk difference R2 - R4
        rd = (t.a_only - t.b_only) / float(n) if n > 0 else 0.0
        paired_pairs = list(zip(r2_seq, r4_seq))
        rd_boot = bootstrap(
            paired_pairs,
            statistic=lambda s: sum(a - b for a, b in s) / float(len(s)),
            n_resamples=n_resamples,
            seed=seed,
        )

        # Odds ratio b / c
        b, c = t.a_only, t.b_only
        if c > 0 and b > 0:
            or_val = b / float(c)
            se_ln = math.sqrt(1.0 / b + 1.0 / c)
            or_ci = [math.exp(math.log(or_val) - 1.96 * se_ln), math.exp(math.log(or_val) + 1.96 * se_ln)]
        elif c == 0 and b > 0:
            or_val = float("inf")
            or_ci = [0.0, float("inf")]
        else:
            or_val = 0.0
            or_ci = [0.0, 0.0]

        mcnemar_block = {
            "b": b,
            "c": c,
            "chi2_p_value": chi2_p,
            "chi2_statistic": chi2_stat,
            "continuity_correction": True,
            "exact_p_value": exact_p,
            "n_discordant": b + c,
            "p_value": exact_p,  # Primary p-value is exact
            "primary_p_label": "exact_binomial_two_sided",
            "primary_p_value": exact_p,
            "secondary_p_label": "chi2_with_continuity_correction",
            "secondary_p_value": chi2_p,
            "significant_at_0.05": exact_p < 0.05,
            "table": table_dict,
        }

        return {
            "mean_difference": round(mean_d, 6),
            "mcnemar": mcnemar_block,
            "mode": mode_name,
            "odds_ratio": round(or_val, 6) if or_val != float("inf") else "inf",
            "odds_ratio_ci": [round(or_ci[0], 6), round(or_ci[1], 6) if or_ci[1] != float("inf") else "inf"],
            "odds_ratio_method": "matched_pairs_odds_ratio_b_div_c_with_lognormal_ci",
            "paired_d_z": round(dz, 6),
            "paired_d_z_method": "paired_cohen_d_z_mean_diff_div_sample_sd_ddof_1",
            "risk_difference": round(rd, 6),
            "risk_difference_bootstrap_ci": [round(rd_boot[0], 6), round(rd_boot[1], 6)],
            "risk_difference_method": f"scenario_paired_risk_difference_bootstrap_{n_resamples}_seed{seed}",
            "sd_difference": round(sd_d, 6),
            "table": table_dict,
            "ties": ties_count,
        }

    # Mode 1: all-3-pass
    r2_all3 = [all(row) for row in r2_matrix]
    r4_all3 = [all(row) for row in r4_matrix]
    comp_all3 = run_sub_comparison(r2_all3, r4_all3, "all_3_pass")

    # Mode 2: trial-1 pass
    r2_t1 = [row[0] for row in r2_matrix]
    r4_t1 = [row[0] for row in r4_matrix]
    comp_t1 = run_sub_comparison(r2_t1, r4_t1, "trial_1_pass")

    return {
        "all_3_pass": comp_all3,
        "trial_1_pass": comp_t1,
    }


def compute_order_effects(
    matrix_dict: Dict[str, List[bool]],
    retained_bases: List[str],
    manifest_150: List[str],
    seed: int = SEED,
    n_permutations: int = N_RESAMPLES,
) -> Dict[str, Any]:
    """Compute order-effect correlation between manifest index and scenario success count."""
    manifest_pos = {b: idx for idx, b in enumerate(manifest_150)}
    pairs = [
        (manifest_pos[b], sum(matrix_dict[b]))
        for b in retained_bases
        if b in manifest_pos and b in matrix_dict
    ]
    n = len(pairs)
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]

    def rank_vector(vec: Sequence[float | int]) -> List[float]:
        sorted_idx = sorted(range(len(vec)), key=lambda i: vec[i])
        ranks = [0.0] * len(vec)
        i = 0
        while i < len(vec):
            j = i
            while j < len(vec) and vec[sorted_idx[j]] == vec[sorted_idx[i]]:
                j += 1
            avg_rank = (i + j - 1) / 2.0 + 1.0
            for k in range(i, j):
                ranks[sorted_idx[k]] = avg_rank
            i = j
        return ranks

    def corr(a: Sequence[float], b: Sequence[float]) -> float:
        ma = sum(a) / len(a)
        mb = sum(b) / len(b)
        num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
        den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
        return num / den if den > 0 else 0.0

    r_spearman = corr(rank_vector(xs), rank_vector(ys))
    r_pearson = corr(xs, ys)

    rng = random.Random(seed)
    x_ranks = rank_vector(xs)
    y_ranks_perm = list(rank_vector(ys))
    perm_count = 0
    for _ in range(n_permutations):
        rng.shuffle(y_ranks_perm)
        sim_r = corr(x_ranks, y_ranks_perm)
        if abs(sim_r) >= abs(r_spearman):
            perm_count += 1
    perm_p = perm_count / float(n_permutations)

    # First vs second half split by manifest order
    sorted_pairs = sorted(pairs, key=lambda p: p[0])
    half = n // 2
    first_half = sorted_pairs[:half]
    second_half = sorted_pairs[half:]
    all3_first = sum(1 for p in first_half if p[1] == 3)
    all3_second = sum(1 for p in second_half if p[1] == 3)

    return {
        "all_3_pass_first_half": all3_first,
        "all_3_pass_second_half": all3_second,
        "first_half_n": len(first_half),
        "manifest_order_note": (
            "R4 infra_excluded drops 33 scenarios: r-0305 (k3 timeout), r-0310 (k2 timeout), "
            "and r-0320..r-0350 (all 3 trials dead). Scenarios r-0318 and r-0319 survived, "
            "so the retained 117 scenarios consist of 115 from the first 117 plus r-0318 and r-0319."
        ),
        "method": f"correlation_manifest_index_vs_successes_with_permutation_test_{n_permutations}_seed{seed}",
        "n": n,
        "pearson_r": round(r_pearson, 4),
        "permutation_p": round(perm_p, 4),
        "second_half_n": len(second_half),
        "spearman_rho": round(r_spearman, 4),
    }


def adjust_holm_family(family: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply Holm-Bonferroni step-down correction to a list of tests.
    
    Never emits 0.0: preserves exact floats and uses '<1e-15' if underflowed.
    """
    m = len(family)
    sorted_indices = sorted(range(m), key=lambda i: family[i]["raw_p_value"])
    prev_adj = 0.0
    adjusted_map: Dict[int, Tuple[Any, bool]] = {}

    for rank, orig_idx in enumerate(sorted_indices):
        mult = m - rank
        raw_p = family[orig_idx]["raw_p_value"]
        adj = min(1.0, max(prev_adj, mult * raw_p))
        prev_adj = adj
        if adj < 1e-15:
            adj_repr: Any = "<1e-15"
        else:
            adj_repr = round(adj, 8) if adj >= 1e-6 else adj
        adjusted_map[orig_idx] = (adj_repr, adj < 0.05)

    results = []
    for orig_idx, t in enumerate(family):
        raw_p = t["raw_p_value"]
        if raw_p < 1e-15:
            raw_repr: Any = "<1e-15"
        else:
            raw_repr = round(raw_p, 8) if raw_p >= 1e-6 else raw_p

        adj_val, sig = adjusted_map[orig_idx]
        results.append({
            "description": t["description"],
            "holm_adjusted_p_value": adj_val,
            "raw_p_source": t["raw_p_source"],
            "raw_p_value": raw_repr,
            "significant_at_0.05": sig,
            "test": t["test"],
        })
    return results


def compute_hypotheses_and_holm(
    r2_as_run: Dict[str, Any],
    r4_as_run: Dict[str, Any],
    paired_as_run: Dict[str, Any],
    r2_infra: Dict[str, Any],
    r4_infra: Dict[str, Any],
    paired_infra: Dict[str, Any],
    r2_strict: Dict[str, Any],
    r4_strict: Dict[str, Any],
    paired_strict: Dict[str, Any],
    paired_scenarios_as_run: List[Tuple[List[bool], List[bool]]],
    seed: int = SEED,
    n_resamples: int = N_RESAMPLES,
) -> Dict[str, Any]:
    """Evaluate H4, H5, and Holm families without using the word FALSIFIED."""
    # H4: Pre-registered criterion requires >= 4 of 6 rungs. Only 2 rungs valid.
    def evaluate_h4_details(r2_st: Dict[str, Any], r4_st: Dict[str, Any]) -> Dict[str, Any]:
        r2_p3 = r2_st["pass_k"]["k3"]["pass_hat_k"]
        r2_naive = r2_st["pass_k"]["k3"]["naive_k"]
        r2_w_ci = wilson_interval(r2_st["concentration_counts"]["always_pass"], r2_st["concentration_counts"]["total_scenarios"])
        r2_contains = r2_w_ci[0] <= r2_naive <= r2_w_ci[1]
        r2_exceeds = r2_w_ci[0] > r2_naive

        r4_p3 = r4_st["pass_k"]["k3"]["pass_hat_k"]
        r4_naive = r4_st["pass_k"]["k3"]["naive_k"]
        r4_w_ci = wilson_interval(r4_st["concentration_counts"]["always_pass"], r4_st["concentration_counts"]["total_scenarios"])
        r4_contains = r4_w_ci[0] <= r4_naive <= r4_w_ci[1]
        r4_exceeds = r4_w_ci[0] > r4_naive

        return {
            "R2": {
                "contains_naive": r2_contains,
                "exceeds_naive": r2_exceeds,
                "measured_pass3": round(r2_p3, 4),
                "naive_p3": round(r2_naive, 4),
                "wilson_ci": [round(r2_w_ci[0], 4), round(r2_w_ci[1], 4)],
            },
            "R4": {
                "contains_naive": r4_contains,
                "exceeds_naive": r4_exceeds,
                "measured_pass3": round(r4_p3, 4),
                "naive_p3": round(r4_naive, 4),
                "wilson_ci": [round(r4_w_ci[0], 4), round(r4_w_ci[1], 4)],
            },
        }

    h4_as_run_det = evaluate_h4_details(r2_as_run, r4_as_run)
    h4_infra_det = evaluate_h4_details(r2_infra, r4_infra)
    h4_strict_det = evaluate_h4_details(r2_strict, r4_strict)

    # Bootstrap CI for delta difference (R4 - R2)
    def calc_delta(mat: Sequence[List[bool]]) -> float:
        n = len(mat)
        tot_trials = n * len(mat[0]) if n > 0 else 0
        passes = sum(sum(r) for r in mat)
        p1 = passes / float(tot_trials) if tot_trials > 0 else 0.0
        p3 = sum(1 for r in mat if all(r)) / float(n) if n > 0 else 0.0
        return p3 - (p1 ** 3)

    def diff_delta_stat(sample: Sequence[Tuple[List[bool], List[bool]]]) -> float:
        s2 = [p[0] for p in sample]
        s4 = [p[1] for p in sample]
        return calc_delta(s4) - calc_delta(s2)

    diff_delta_ci = bootstrap(
        paired_scenarios_as_run,
        statistic=diff_delta_stat,
        n_resamples=n_resamples,
        seed=seed,
    )

    r2_delta_as = r2_as_run["pass_k"]["k3"]["deviation_delta"]
    r4_delta_as = r4_as_run["pass_k"]["k3"]["deviation_delta"]
    diff_delta_val = r4_delta_as - r2_delta_as

    r2_delta_inf = r2_infra["pass_k"]["k3"]["deviation_delta"]
    r4_delta_inf = r4_infra["pass_k"]["k3"]["deviation_delta"]

    h4_block = {
        "details": h4_as_run_det,
        "details_infra_excluded": h4_infra_det,
        "details_infra_excluded_strict": h4_strict_det,
        "per_rung_criterion_met": {
            "as_run": {"R2": False, "R4": True},
            "infra_excluded": {"R2": False, "R4": True},
            "infra_excluded_strict": {"R2": False, "R4": True},
        },
        "preregistered_falsified_by": "Wilson CI of measured contains the naive point for >=3 rungs",
        "preregistered_text": "Measured pass³ exceeds naive (pass@1)³ for ≥4 of 6 rungs",
        "reason": "only 2 of 6 rungs valid; criterion requires >=4 of 6",
        "recomputed_verdict": "NOT_TESTABLE_AS_PREREGISTERED",
        "rungs_disjoint_count": 1,
        "rungs_evaluated": ["R2", "R4"],
        "rungs_exceeding_naive": ["R4"],
        "sensitivity_verdict_infra_excluded": "NOT_TESTABLE_AS_PREREGISTERED",
        "sensitivity_verdict_infra_excluded_strict": "NOT_TESTABLE_AS_PREREGISTERED",
        "status": "NOT_TESTABLE_AS_PREREGISTERED",
    }

    h5_block = {
        "delta_difference_R4_minus_R2": {
            "bootstrap_ci": [round(diff_delta_ci[0], 6), round(diff_delta_ci[1], 6)],
            "difference": round(diff_delta_val, 6),
            "method": f"paired_scenario_bootstrap_delta_difference_{n_resamples}_seed{seed}",
        },
        "details": {
            "R2_cheap": {
                "concentration_ratio": r2_as_run["pass_k"]["k3"]["concentration_ratio_C_k"],
                "deviation_delta": r2_delta_as,
                "deviation_delta_bootstrap_ci": r2_as_run["pass_k"]["k3"]["deviation_delta_bootstrap_ci"],
            },
            "R4_frontier": {
                "concentration_ratio": r4_as_run["pass_k"]["k3"]["concentration_ratio_C_k"],
                "deviation_delta": r4_delta_as,
                "deviation_delta_bootstrap_ci": r4_as_run["pass_k"]["k3"]["deviation_delta_bootstrap_ci"],
            },
        },
        "details_infra_excluded": {
            "R2_cheap": {
                "concentration_ratio": r2_infra["pass_k"]["k3"]["concentration_ratio_C_k"],
                "deviation_delta": r2_delta_inf,
                "deviation_delta_bootstrap_ci": r2_infra["pass_k"]["k3"]["deviation_delta_bootstrap_ci"],
            },
            "R4_frontier": {
                "concentration_ratio": r4_infra["pass_k"]["k3"]["concentration_ratio_C_k"],
                "deviation_delta": r4_delta_inf,
                "deviation_delta_bootstrap_ci": r4_infra["pass_k"]["k3"]["deviation_delta_bootstrap_ci"],
            },
        },
        "preregistered_falsified_by": "rank correlation across the ladder is null or reversed",
        "preregistered_text": "Deviation from naive is larger for cheap rungs than frontier",
        "reason": (
            "requires multi-tier ladder across >=4 rungs; with 2 valid rungs, rank correlation is degenerate "
            "and observed point estimates (delta_R2 = -0.0247 vs delta_R4 = +0.0167) have overlapping bootstrap CIs."
        ),
        "recomputed_verdict": "NOT_TESTABLE_AS_PREREGISTERED (2 rungs)",
        "sensitivity_verdict_infra_excluded": "NOT_TESTABLE_AS_PREREGISTERED (2 rungs)",
        "sensitivity_verdict_infra_excluded_strict": "NOT_TESTABLE_AS_PREREGISTERED (2 rungs)",
        "status": "NOT_TESTABLE_AS_PREREGISTERED (2 rungs)",
    }

    # B. HOLM FAMILIES
    # Primary declared paper-wide family of 5 tests
    paper_family = [
        {
            "description": "Chi-square independence goodness-of-fit against Binomial(3, p) on R2 (parametric bootstrap)",
            "raw_p_source": "rungs.R2.as_run.independence_test.parametric_bootstrap_p_value",
            "raw_p_value": r2_as_run["independence_test"]["parametric_bootstrap_p_value"],
            "test": "independence_goodness_of_fit_R2",
        },
        {
            "description": "Chi-square independence goodness-of-fit against Binomial(3, p) on R4 as-run (parametric bootstrap)",
            "raw_p_source": "rungs.R4.as_run.independence_test.parametric_bootstrap_p_value",
            "raw_p_value": r4_as_run["independence_test"]["parametric_bootstrap_p_value"],
            "test": "independence_goodness_of_fit_R4_as_run",
        },
        {
            "description": "Chi-square independence goodness-of-fit against Binomial(3, p) on R4 infra-excluded (parametric bootstrap)",
            "raw_p_source": "rungs.R4.infra_excluded.independence_test.parametric_bootstrap_p_value",
            "raw_p_value": r4_infra["independence_test"]["parametric_bootstrap_p_value"],
            "test": "independence_goodness_of_fit_R4_infra_excluded",
        },
        {
            "description": "Paired McNemar test on R2 vs R4 per-scenario all-3-pass as-run (exact p)",
            "raw_p_source": "paired_comparisons.R2_vs_R4.as_run.all_3_pass.mcnemar.exact_p_value",
            "raw_p_value": paired_as_run["all_3_pass"]["mcnemar"]["exact_p_value"],
            "test": "paired_mcnemar_R2_vs_R4_all_3_pass",
        },
        {
            "description": "Paired McNemar test on R2 vs R4 per-scenario trial-1 pass as-run (exact p)",
            "raw_p_source": "paired_comparisons.R2_vs_R4.as_run.trial_1_pass.mcnemar.exact_p_value",
            "raw_p_value": paired_as_run["trial_1_pass"]["mcnemar"]["exact_p_value"],
            "test": "paired_mcnemar_R2_vs_R4_trial_1_pass",
        },
    ]

    family_as_run = [
        {
            "description": "Paired McNemar test on R2 vs R4 per-scenario trial-1 pass as-run (exact p)",
            "raw_p_source": "paired_comparisons.R2_vs_R4.as_run.trial_1_pass.mcnemar.exact_p_value",
            "raw_p_value": paired_as_run["trial_1_pass"]["mcnemar"]["exact_p_value"],
            "test": "paired_mcnemar_R2_vs_R4_trial_1_pass",
        },
        {
            "description": "Paired McNemar test on R2 vs R4 per-scenario all-3-pass as-run (exact p)",
            "raw_p_source": "paired_comparisons.R2_vs_R4.as_run.all_3_pass.mcnemar.exact_p_value",
            "raw_p_value": paired_as_run["all_3_pass"]["mcnemar"]["exact_p_value"],
            "test": "paired_mcnemar_R2_vs_R4_all_3_pass",
        },
        {
            "description": "Chi-square independence goodness-of-fit against Binomial(3, p) on R4 as-run (parametric bootstrap)",
            "raw_p_source": "rungs.R4.as_run.independence_test.parametric_bootstrap_p_value",
            "raw_p_value": r4_as_run["independence_test"]["parametric_bootstrap_p_value"],
            "test": "independence_goodness_of_fit_R4",
        },
        {
            "description": "Chi-square independence goodness-of-fit against Binomial(3, p) on R2 as-run (parametric bootstrap)",
            "raw_p_source": "rungs.R2.as_run.independence_test.parametric_bootstrap_p_value",
            "raw_p_value": r2_as_run["independence_test"]["parametric_bootstrap_p_value"],
            "test": "independence_goodness_of_fit_R2",
        },
    ]

    family_infra = [
        {
            "description": "Paired McNemar test on R2 vs R4 per-scenario trial-1 pass infra-excluded (exact p)",
            "raw_p_source": "paired_comparisons.R2_vs_R4.infra_excluded.trial_1_pass.mcnemar.exact_p_value",
            "raw_p_value": paired_infra["trial_1_pass"]["mcnemar"]["exact_p_value"],
            "test": "paired_mcnemar_R2_vs_R4_trial_1_pass",
        },
        {
            "description": "Paired McNemar test on R2 vs R4 per-scenario all-3-pass infra-excluded (exact p)",
            "raw_p_source": "paired_comparisons.R2_vs_R4.infra_excluded.all_3_pass.mcnemar.exact_p_value",
            "raw_p_value": paired_infra["all_3_pass"]["mcnemar"]["exact_p_value"],
            "test": "paired_mcnemar_R2_vs_R4_all_3_pass",
        },
        {
            "description": "Chi-square independence goodness-of-fit against Binomial(3, p) on R4 infra-excluded (parametric bootstrap)",
            "raw_p_source": "rungs.R4.infra_excluded.independence_test.parametric_bootstrap_p_value",
            "raw_p_value": r4_infra["independence_test"]["parametric_bootstrap_p_value"],
            "test": "independence_goodness_of_fit_R4",
        },
        {
            "description": "Chi-square independence goodness-of-fit against Binomial(3, p) on R2 (parametric bootstrap)",
            "raw_p_source": "rungs.R2.as_run.independence_test.parametric_bootstrap_p_value",
            "raw_p_value": r2_as_run["independence_test"]["parametric_bootstrap_p_value"],
            "test": "independence_goodness_of_fit_R2",
        },
    ]

    family_strict = [
        {
            "description": "Paired McNemar test on R2 vs R4 per-scenario trial-1 pass infra-excluded-strict (exact p)",
            "raw_p_source": "paired_comparisons.R2_vs_R4.infra_excluded_strict.trial_1_pass.mcnemar.exact_p_value",
            "raw_p_value": paired_strict["trial_1_pass"]["mcnemar"]["exact_p_value"],
            "test": "paired_mcnemar_R2_vs_R4_trial_1_pass",
        },
        {
            "description": "Paired McNemar test on R2 vs R4 per-scenario all-3-pass infra-excluded-strict (exact p)",
            "raw_p_source": "paired_comparisons.R2_vs_R4.infra_excluded_strict.all_3_pass.mcnemar.exact_p_value",
            "raw_p_value": paired_strict["all_3_pass"]["mcnemar"]["exact_p_value"],
            "test": "paired_mcnemar_R2_vs_R4_all_3_pass",
        },
        {
            "description": "Chi-square independence goodness-of-fit against Binomial(3, p) on R4 infra-excluded-strict (parametric bootstrap)",
            "raw_p_source": "rungs.R4.infra_excluded_strict.independence_test.parametric_bootstrap_p_value",
            "raw_p_value": r4_strict["independence_test"]["parametric_bootstrap_p_value"],
            "test": "independence_goodness_of_fit_R4",
        },
        {
            "description": "Chi-square independence goodness-of-fit against Binomial(3, p) on R2 infra-excluded-strict (parametric bootstrap)",
            "raw_p_source": "rungs.R2.infra_excluded_strict.independence_test.parametric_bootstrap_p_value",
            "raw_p_value": r2_strict["independence_test"]["parametric_bootstrap_p_value"],
            "test": "independence_goodness_of_fit_R2",
        },
    ]

    return {
        "H4": h4_block,
        "H5": h5_block,
        "family_of_tests": adjust_holm_family(paper_family),
        "family_of_tests_as_run": adjust_holm_family(family_as_run),
        "family_of_tests_infra_excluded": adjust_holm_family(family_infra),
        "family_of_tests_infra_excluded_strict": adjust_holm_family(family_strict),
    }


def compute_attempts_summary(
    trace_db_path: Path,
    ledger_path: Path,
) -> Dict[str, Any]:
    """Compute attempt segmentation summary for Pass 1 (cap 12) vs Pass 2 (cap 24).
    
    Per Decision D-010: trace.db holds two attempts per run. Pass 1 tokens (~18.9M)
    are discarded spend from an earlier cap-12 sweep. Pass 2 tokens (~35.4M) represent
    the final cap-24 evaluation.
    """
    conn = sqlite3.connect(trace_db_path)
    try:
        ledger_rows = []
        if ledger_path.exists():
            with open(ledger_path, "r", encoding="utf-8") as f:
                ledger_rows = [json.loads(line) for line in f if line.strip()]

        attempts_summary: Dict[str, Any] = {
            "pass_1": {"cap": 12, "rungs": {}},
            "pass_2": {"cap": 24, "rungs": {}},
        }

        for rung_label, run_id in [("R2", "p06_r2_7e0a1b79"), ("R4", "p06_r4_7e0a1b79")]:
            rows = conn.execute(
                """
                SELECT scenario_id, step_index, prompt_tokens, completion_tokens, latency_ms, termination_reason, verdict, timestamp
                FROM spans WHERE run_id = ? ORDER BY scenario_id, timestamp ASC
                """,
                (run_id,),
            ).fetchall()

            by_sid: Dict[str, List[List[Tuple[Any, ...]]]] = {}
            for r in rows:
                sid, s_idx, pt, ct, lat, term, verd, ts = r
                att = by_sid.setdefault(sid, [[]])
                if len(att[-1]) > 0 and s_idx <= 1 and ts > att[-1][-1][7]:
                    att.append([])
                att[-1].append(r)

            # Pass 1
            p1_spans = [s for atts in by_sid.values() if len(atts) > 1 for s in atts[0]]
            p1_pt = sum(s[2] or 0 for s in p1_spans)
            p1_ct = sum(s[3] or 0 for s in p1_spans)
            p1_ts = [s[7] for s in p1_spans]
            p1_spend = sum(
                r.get("usd", 0.0)
                for r in ledger_rows
                if r.get("rung") == rung_label and r.get("timestamp_utc", "") < "2026-09-11T18:00:00"
            )

            attempts_summary["pass_1"]["rungs"][rung_label] = {
                "completion_tokens": p1_ct,
                "prompt_tokens": p1_pt,
                "runs_count": len([atts for atts in by_sid.values() if len(atts) > 1]),
                "spend_usd": round(p1_spend, 4),
                "time_window": [min(p1_ts), max(p1_ts)] if p1_ts else None,
                "total_tokens": p1_pt + p1_ct,
            }

            # Pass 2
            p2_spans = [s for atts in by_sid.values() for s in atts[-1]]
            p2_pt = sum(s[2] or 0 for s in p2_spans)
            p2_ct = sum(s[3] or 0 for s in p2_spans)
            p2_ts = [s[7] for s in p2_spans]
            p2_spend = sum(
                r.get("usd", 0.0)
                for r in ledger_rows
                if r.get("rung") == rung_label and r.get("timestamp_utc", "") >= "2026-09-11T18:00:00"
            )

            attempts_summary["pass_2"]["rungs"][rung_label] = {
                "completion_tokens": p2_ct,
                "prompt_tokens": p2_pt,
                "runs_count": len(by_sid),
                "spend_usd": round(p2_spend, 4),
                "time_window": [min(p2_ts), max(p2_ts)] if p2_ts else None,
                "total_tokens": p2_pt + p2_ct,
            }

        p1_tokens = sum(r["total_tokens"] for r in attempts_summary["pass_1"]["rungs"].values())
        p1_spend = sum(r["spend_usd"] for r in attempts_summary["pass_1"]["rungs"].values())
        p1_min_ts = min(r["time_window"][0] for r in attempts_summary["pass_1"]["rungs"].values() if r["time_window"])
        p1_max_ts = max(r["time_window"][1] for r in attempts_summary["pass_1"]["rungs"].values() if r["time_window"])
        attempts_summary["pass_1"]["time_window"] = [p1_min_ts, p1_max_ts]
        attempts_summary["pass_1"]["total_discarded_spend_usd"] = round(p1_spend, 4)
        attempts_summary["pass_1"]["total_discarded_tokens"] = p1_tokens

        p2_tokens = sum(r["total_tokens"] for r in attempts_summary["pass_2"]["rungs"].values())
        p2_spend = sum(r["spend_usd"] for r in attempts_summary["pass_2"]["rungs"].values())
        p2_min_ts = min(r["time_window"][0] for r in attempts_summary["pass_2"]["rungs"].values() if r["time_window"])
        p2_max_ts = max(r["time_window"][1] for r in attempts_summary["pass_2"]["rungs"].values() if r["time_window"])
        attempts_summary["pass_2"]["time_window"] = [p2_min_ts, p2_max_ts]
        attempts_summary["pass_2"]["total_final_spend_usd"] = round(p2_spend, 4)
        attempts_summary["pass_2"]["total_final_tokens"] = p2_tokens

        attempts_summary["total"] = {
            "discarded_token_percentage": round(100.0 * p1_tokens / (p1_tokens + p2_tokens), 2) if (p1_tokens + p2_tokens) > 0 else 0.0,
            "grand_total_spend_usd": round(p1_spend + p2_spend, 4),
            "grand_total_tokens": p1_tokens + p2_tokens,
        }
        return attempts_summary
    finally:
        conn.close()


def print_summary_table(results: Dict[str, Any]) -> None:
    """Print clean ASCII summary table to stdout."""
    print("=" * 115)
    print("PROJECT P06: PASS^K RELIABILITY AND CONCENTRATION ANALYSIS (AFTER STATISTICAL REVIEW)")
    print("=" * 115)
    header = f"{'Metric':<32} | {'R2 (as-run, n=150)':<22} | {'R4 (as-run, n=150)':<22} | {'R4 (infra-excl, n=117)':<22}"
    print(header)
    print("-" * 115)
    
    r2_as = results["rungs"]["R2"]["as_run"]
    r4_as = results["rungs"]["R4"]["as_run"]
    r4_inf = results["rungs"]["R4"]["infra_excluded"]

    def fmt_ci(val: float, ci: List[float]) -> str:
        return f"{val:.4f} [{ci[0]:.4f}, {ci[1]:.4f}]"

    print(f"{'pass@1 (pooled, Wilson CI)':<32} | {fmt_ci(r2_as['pass_at_1']['score'], r2_as['pass_at_1']['wilson_ci']):<22} | {fmt_ci(r4_as['pass_at_1']['score'], r4_as['pass_at_1']['wilson_ci']):<22} | {fmt_ci(r4_inf['pass_at_1']['score'], r4_inf['pass_at_1']['wilson_ci']):<22}")
    print(f"{'pass@1 (scenario boot CI)':<32} | {fmt_ci(r2_as['pass_at_1']['score'], r2_as['pass_at_1']['scenario_bootstrap_ci']):<22} | {fmt_ci(r4_as['pass_at_1']['score'], r4_as['pass_at_1']['scenario_bootstrap_ci']):<22} | {fmt_ci(r4_inf['pass_at_1']['score'], r4_inf['pass_at_1']['scenario_bootstrap_ci']):<22}")
    print(f"{'pass_hat_2 (first 2 trials)':<32} | {fmt_ci(r2_as['pass_k']['k2']['pass_hat_k'], r2_as['pass_k']['k2']['pass_hat_k_bootstrap_ci']):<22} | {fmt_ci(r4_as['pass_k']['k2']['pass_hat_k'], r4_as['pass_k']['k2']['pass_hat_k_bootstrap_ci']):<22} | {fmt_ci(r4_inf['pass_k']['k2']['pass_hat_k'], r4_inf['pass_k']['k2']['pass_hat_k_bootstrap_ci']):<22}")
    print(f"{'naive_p_2':<32} | {r2_as['pass_k']['k2']['naive_k']:<22.4f} | {r4_as['pass_k']['k2']['naive_k']:<22.4f} | {r4_inf['pass_k']['k2']['naive_k']:<22.4f}")
    print(f"{'C_2 (pass_2 / naive_2)':<32} | {fmt_ci(r2_as['pass_k']['k2']['concentration_ratio_C_k'], r2_as['pass_k']['k2']['concentration_ratio_bootstrap_ci']):<22} | {fmt_ci(r4_as['pass_k']['k2']['concentration_ratio_C_k'], r4_as['pass_k']['k2']['concentration_ratio_bootstrap_ci']):<22} | {fmt_ci(r4_inf['pass_k']['k2']['concentration_ratio_C_k'], r4_inf['pass_k']['k2']['concentration_ratio_bootstrap_ci']):<22}")
    print(f"{'pass_hat_3 (all 3 trials)':<32} | {fmt_ci(r2_as['pass_k']['k3']['pass_hat_k'], r2_as['pass_k']['k3']['pass_hat_k_bootstrap_ci']):<22} | {fmt_ci(r4_as['pass_k']['k3']['pass_hat_k'], r4_as['pass_k']['k3']['pass_hat_k_bootstrap_ci']):<22} | {fmt_ci(r4_inf['pass_k']['k3']['pass_hat_k'], r4_inf['pass_k']['k3']['pass_hat_k_bootstrap_ci']):<22}")
    print(f"{'naive_p_3':<32} | {r2_as['pass_k']['k3']['naive_k']:<22.4f} | {r4_as['pass_k']['k3']['naive_k']:<22.4f} | {r4_inf['pass_k']['k3']['naive_k']:<22.4f}")
    print(f"{'C_3 (pass_3 / naive_3)':<32} | {fmt_ci(r2_as['pass_k']['k3']['concentration_ratio_C_k'], r2_as['pass_k']['k3']['concentration_ratio_bootstrap_ci']):<22} | {fmt_ci(r4_as['pass_k']['k3']['concentration_ratio_C_k'], r4_as['pass_k']['k3']['concentration_ratio_bootstrap_ci']):<22} | {fmt_ci(r4_inf['pass_k']['k3']['concentration_ratio_C_k'], r4_inf['pass_k']['k3']['concentration_ratio_bootstrap_ci']):<22}")
    print(f"{'Chi2 GoF stat (df=2, p_param)':<32} | {r2_as['independence_test']['chi2_statistic']:.3f} (p={r2_as['independence_test']['parametric_bootstrap_p_value']:.4f}){'':<7} | {r4_as['independence_test']['chi2_statistic']:.3f} (p={r4_as['independence_test']['parametric_bootstrap_p_value']:.4f}){'':<7} | {r4_inf['independence_test']['chi2_statistic']:.3f} (p={r4_inf['independence_test']['parametric_bootstrap_p_value']:.4f}){'':<7}")
    print(f"{'Tarone Z (score test, p)':<32} | {r2_as['independence_test']['tarone_z_test']['z_statistic']:.3f} (p={r2_as['independence_test']['tarone_z_test']['p_value']:.4f}){'':<7} | {r4_as['independence_test']['tarone_z_test']['z_statistic']:.3f} (p={r4_as['independence_test']['tarone_z_test']['p_value']:.4f}){'':<7} | {r4_inf['independence_test']['tarone_z_test']['z_statistic']:.3f} (p={r4_inf['independence_test']['tarone_z_test']['p_value']:.4f}){'':<7}")
    print(f"{'Exact Binom Tail p':<32} | {r2_as['independence_test']['tail_test']['exact_tail_p_value']:<22.4f} | {r4_as['independence_test']['tail_test']['exact_tail_p_value']:<22.4f} | {r4_inf['independence_test']['tail_test']['exact_tail_p_value']:<22.4f}")
    print(f"{'ICC(1,1) [95% boot CI]':<32} | {fmt_ci(r2_as['intra_scenario_correlation']['icc'], r2_as['intra_scenario_correlation']['icc_bootstrap_ci']):<22} | {fmt_ci(r4_as['intra_scenario_correlation']['icc'], r4_as['intra_scenario_correlation']['icc_bootstrap_ci']):<22} | {fmt_ci(r4_inf['intra_scenario_correlation']['icc'], r4_inf['intra_scenario_correlation']['icc_bootstrap_ci']):<22}")
    r2_c8 = r2_as['intra_scenario_correlation']['extrapolation_table_beta_binomial']['k8']
    r4_c8 = r4_inf['intra_scenario_correlation']['extrapolation_table_beta_binomial']['k8']
    print(f"{'Extrap C_8 (pt / at ICC-hi)':<32} | {r2_c8['concentration_ratio_C_k']:.2f} / {r2_c8['concentration_ratio_at_icc_ci_upper']:.2f}{'':<14} | —                      | {r4_c8['concentration_ratio_C_k']:.2f} / {r4_c8['concentration_ratio_at_icc_ci_upper']:.2f}{'':<14}")
    print(f"{'Fleiss Kappa [95% boot CI]':<32} | {fmt_ci(r2_as['intra_scenario_correlation']['fleiss_kappa'], r2_as['intra_scenario_correlation']['fleiss_kappa_bootstrap_ci']):<22} | {fmt_ci(r4_as['intra_scenario_correlation']['fleiss_kappa'], r4_as['intra_scenario_correlation']['fleiss_kappa_bootstrap_ci']):<22} | {fmt_ci(r4_inf['intra_scenario_correlation']['fleiss_kappa'], r4_inf['intra_scenario_correlation']['fleiss_kappa_bootstrap_ci']):<22}")
    print(f"{'Always Pass / Mixed / Fail':<32} | {r2_as['concentration_counts']['always_pass']}/{r2_as['concentration_counts']['mixed']}/{r2_as['concentration_counts']['always_fail']:<16} | {r4_as['concentration_counts']['always_pass']}/{r4_as['concentration_counts']['mixed']}/{r4_as['concentration_counts']['always_fail']:<16} | {r4_inf['concentration_counts']['always_pass']}/{r4_inf['concentration_counts']['mixed']}/{r4_inf['concentration_counts']['always_fail']:<16}")
    print(f"{'Cost / grounded pass (USD)':<32} | ${r2_as['cost_per_grounded_pass']['cost_per_grounded_pass_usd']:.5f}               | ${r4_as['cost_per_grounded_pass']['cost_per_grounded_pass_usd']:.5f}               | ${r4_inf['cost_per_grounded_pass']['cost_per_grounded_pass_usd']:.5f}")
    print("-" * 115)
    print(f"R6 Status: {results['rungs']['R6']['status']} ({results['rungs']['R6']['evidence']['spans_count']} spans, {results['rungs']['R6']['evidence']['runs_count']} runs, 0 verdicts)")
    print(f"H4 Status: {results['hypotheses']['H4']['status']} · reason: {results['hypotheses']['H4']['reason']}")
    print(f"H5 Status: {results['hypotheses']['H5']['status']} · reason: {results['hypotheses']['H5']['reason']}")
    print("=" * 115)


def run_analysis(
    trace_db_path: Path = Path("projects/p06_passk/trace.db"),
    ledger_path: Path = Path("projects/p06_passk/ledger.jsonl"),
    output_path: Optional[Path] = Path("projects/p06_passk/analysis.json"),
    seed: int = SEED,
    n_resamples: int = N_RESAMPLES,
) -> Dict[str, Any]:
    """Execute complete analysis and write deterministic analysis.json."""
    db_bytes = trace_db_path.read_bytes()
    db_sha256 = hashlib.sha256(db_bytes).hexdigest()

    # Load trial matrices
    r2_matrix_dict, _, _, _ = load_scenario_trial_matrix(trace_db_path, "p06_r2_7e0a1b79")
    r4_matrix_dict, _, _, _ = load_scenario_trial_matrix(trace_db_path, "p06_r4_7e0a1b79")
    _, r6_spans, r6_runs, r6_verdicts = load_scenario_trial_matrix(trace_db_path, "p06_r6_7e0a1b79")

    # Terminal state classification & drop sets
    r2_term = classify_terminal_states(trace_db_path, "p06_r2_7e0a1b79")
    r4_term = classify_terminal_states(trace_db_path, "p06_r4_7e0a1b79")

    # Backwards-compatible dead trial info
    r2_infra = detect_infra_dead_trials(trace_db_path, "p06_r2_7e0a1b79")
    r4_infra = detect_infra_dead_trials(trace_db_path, "p06_r4_7e0a1b79")

    all_bases = sorted(list(set(r2_matrix_dict.keys()) | set(r4_matrix_dict.keys())))

    # 1. as_run (all 150 scenarios)
    r2_as_run_bases = sorted(r2_matrix_dict.keys())
    r4_as_run_bases = sorted(r4_matrix_dict.keys())
    r2_as_run_matrix = [r2_matrix_dict[b] for b in r2_as_run_bases]
    r4_as_run_matrix = [r4_matrix_dict[b] for b in r4_as_run_bases]

    # 2. infra_excluded (drop scenarios with any dead_at_start trial; R2 n=150, R4 n=117)
    r2_infra_bases = [b for b in r2_as_run_bases if b not in r2_infra["dead_base_scenarios"]]
    r4_infra_bases = [b for b in r4_as_run_bases if b not in r4_infra["dead_base_scenarios"]]
    r2_infra_matrix = [r2_matrix_dict[b] for b in r2_infra_bases]
    r4_infra_matrix = [r4_matrix_dict[b] for b in r4_infra_bases]

    # 3. infra_excluded_strict (drop scenarios with dead_at_start OR midrun_no_completion; R2 n=103, R4 n=67)
    r2_strict_bases = r2_term["strict_retained_scenarios"]
    r4_strict_bases = r4_term["strict_retained_scenarios"]
    r2_strict_matrix = [r2_matrix_dict[b] for b in r2_strict_bases]
    r4_strict_matrix = [r4_matrix_dict[b] for b in r4_strict_bases]

    def analyze_rung_variant(
        matrix_dict: Dict[str, List[bool]],
        retained_bases: List[str],
        rung: str,
    ) -> Dict[str, Any]:
        scenario_matrix = [matrix_dict[b] for b in retained_bases]
        return {
            "concentration_counts": compute_concentration_counts(scenario_matrix),
            "cost_per_grounded_pass": compute_cost_per_grounded_pass(scenario_matrix, ledger_path, rung, seed=seed, n_resamples=n_resamples),
            "independence_test": compute_independence_test(scenario_matrix, seed=seed, n_mc_draws=n_resamples),
            "intra_scenario_correlation": compute_intra_scenario_correlation(scenario_matrix, seed=seed, n_resamples=n_resamples),
            "n_scenarios": len(retained_bases),
            "order_effects": compute_order_effects(matrix_dict, retained_bases, all_bases, seed=seed, n_permutations=n_resamples),
            "pass_at_1": compute_pass_at_1(scenario_matrix, seed=seed, n_resamples=n_resamples),
            "pass_k": {
                "k2": compute_pass_k(scenario_matrix, 2, seed=seed, n_resamples=n_resamples),
                "k3": compute_pass_k(scenario_matrix, 3, seed=seed, n_resamples=n_resamples),
            },
            "retained_scenario_ids": list(retained_bases),
        }

    # R2 variants
    r2_as_run_stats = analyze_rung_variant(r2_matrix_dict, r2_as_run_bases, "R2")
    r2_infra_stats = r2_as_run_stats if len(r2_infra_bases) == len(r2_as_run_bases) else analyze_rung_variant(r2_matrix_dict, r2_infra_bases, "R2")
    r2_strict_stats = analyze_rung_variant(r2_matrix_dict, r2_strict_bases, "R2")

    # R4 variants
    r4_as_run_stats = analyze_rung_variant(r4_matrix_dict, r4_as_run_bases, "R4")
    r4_infra_stats = analyze_rung_variant(r4_matrix_dict, r4_infra_bases, "R4")
    r4_strict_stats = analyze_rung_variant(r4_matrix_dict, r4_strict_bases, "R4")

    # Live trial pass rates
    r2_non_dead = len(r2_as_run_matrix) * 3 - r2_infra["infra_dead_trials"]
    r2_passes_non_dead = sum(sum(r) for r in r2_as_run_matrix)
    r2_live_pass = round(r2_passes_non_dead / float(r2_non_dead), 4) if r2_non_dead > 0 else 0.0

    r4_non_dead = len(r4_as_run_matrix) * 3 - r4_infra["infra_dead_trials"]
    r4_passes_non_dead = sum(sum(r) for r in r4_as_run_matrix)
    r4_live_pass = round(r4_passes_non_dead / float(r4_non_dead), 4) if r4_non_dead > 0 else 0.0

    r2_rung_block = {
        "as_run": r2_as_run_stats,
        "infra_dead_scenarios": r2_infra["infra_dead_scenarios"],
        "infra_dead_scenarios_all3": r2_infra["infra_dead_scenarios_all3"],
        "infra_dead_trials": r2_infra["infra_dead_trials"],
        "infra_excluded": r2_infra_stats,
        "infra_excluded_strict": r2_strict_stats,
        "live_trial_pass_at_1": r2_live_pass,
        "per_trial_split": r2_infra["per_trial_split"],
        "terminal_state_classification": r2_term,
        "time_window": r2_infra["time_window"],
    }

    r4_rung_block = {
        "as_run": r4_as_run_stats,
        "infra_dead_scenarios": r4_infra["infra_dead_scenarios"],
        "infra_dead_scenarios_all3": r4_infra["infra_dead_scenarios_all3"],
        "infra_dead_trials": r4_infra["infra_dead_trials"],
        "infra_excluded": r4_infra_stats,
        "infra_excluded_strict": r4_strict_stats,
        "live_trial_pass_at_1": r4_live_pass,
        "per_trial_split": r4_infra["per_trial_split"],
        "terminal_state_classification": r4_term,
        "time_window": r4_infra["time_window"],
    }

    # R6 status
    r6_stats = {
        "evidence": {
            "reason": "gateway step 1 failure (infrastructure)",
            "runs_count": r6_runs,
            "spans_count": r6_spans,
            "verdicts_count": r6_verdicts,
        },
        "status": "infra_invalid",
    }

    # Paired comparisons across variants
    # as_run paired
    paired_as_run = compute_paired_comparison(r2_as_run_matrix, r4_as_run_matrix, seed=seed, n_resamples=n_resamples)
    paired_as_run["n_scenarios"] = len(all_bases)
    paired_as_run["retained_scenario_ids"] = list(all_bases)

    # infra_excluded paired
    both_infra_bases = [b for b in all_bases if b in r2_infra_bases and b in r4_infra_bases]
    r2_p_inf = [r2_matrix_dict[b] for b in both_infra_bases]
    r4_p_inf = [r4_matrix_dict[b] for b in both_infra_bases]
    paired_infra = compute_paired_comparison(r2_p_inf, r4_p_inf, seed=seed, n_resamples=n_resamples)
    paired_infra["n_scenarios"] = len(both_infra_bases)
    paired_infra["retained_scenario_ids"] = list(both_infra_bases)

    # infra_excluded_strict paired
    both_strict_bases = [b for b in all_bases if b in r2_strict_bases and b in r4_strict_bases]
    r2_p_strict = [r2_matrix_dict[b] for b in both_strict_bases]
    r4_p_strict = [r4_matrix_dict[b] for b in both_strict_bases]
    paired_strict = compute_paired_comparison(r2_p_strict, r4_p_strict, seed=seed, n_resamples=n_resamples)
    paired_strict["n_scenarios"] = len(both_strict_bases)
    paired_strict["retained_scenario_ids"] = list(both_strict_bases)

    paired_stats = {
        "as_run": paired_as_run,
        "infra_excluded": paired_infra,
        "infra_excluded_strict": paired_strict,
    }

    paired_scenarios_as_run = list(zip(r2_as_run_matrix, r4_as_run_matrix))

    # Hypotheses evaluation & Holm correction
    hypotheses_stats = compute_hypotheses_and_holm(
        r2_as_run_stats,
        r4_as_run_stats,
        paired_as_run,
        r2_infra_stats,
        r4_infra_stats,
        paired_infra,
        r2_strict_stats,
        r4_strict_stats,
        paired_strict,
        paired_scenarios_as_run,
        seed=seed,
        n_resamples=n_resamples,
    )

    # Attempts summary (D-010 attempt segmentation)
    attempts_block = compute_attempts_summary(trace_db_path, ledger_path)

    results: Dict[str, Any] = {
        "attempts": attempts_block,
        "generated_from": {
            "trace_db_path": str(trace_db_path),
            "trace_db_sha256": db_sha256,
        },
        "hypotheses": hypotheses_stats,
        "paired_comparisons": {
            "R2_vs_R4": paired_stats,
        },
        "rungs": {
            "R2": r2_rung_block,
            "R4": r4_rung_block,
            "R6": r6_stats,
        },
    }

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, sort_keys=True)

    print_summary_table(results)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="P6 pass^k and concentration statistical analysis")
    parser.add_argument("--db", type=str, default="projects/p06_passk/trace.db", help="Path to trace.db")
    parser.add_argument("--ledger", type=str, default="projects/p06_passk/ledger.jsonl", help="Path to ledger.jsonl")
    parser.add_argument("--out", type=str, default="projects/p06_passk/analysis.json", help="Output analysis.json path")
    parser.add_argument("--seed", type=int, default=SEED, help="Random seed for bootstrap and Monte Carlo")
    parser.add_argument("--resamples", type=int, default=N_RESAMPLES, help="Number of bootstrap resamples and MC draws")

    args = parser.parse_args()
    run_analysis(
        trace_db_path=Path(args.db),
        ledger_path=Path(args.ledger),
        output_path=Path(args.out),
        seed=args.seed,
        n_resamples=args.resamples,
    )


if __name__ == "__main__":
    main()
