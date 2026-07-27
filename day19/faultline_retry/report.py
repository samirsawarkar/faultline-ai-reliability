"""Assemble the Q3 report: sweeps, crossover, recommended region, paired effect, conclusion."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT / "day14") not in sys.path:
    sys.path.insert(0, str(_ROOT / "day14"))

from faultline_stats import mcnemar_from_pairs  # noqa: E402 (Day 14)

from . import sweep as S
from .crossover import (COST_CEILING_AMP, MIN_MARGINAL_SUCCESS, P99_BUDGET,
                        crossover, fail_condition_check)


def build_report() -> Dict[str, Any]:
    indep = S.sweep("independent")
    corr = S.sweep("correlated")
    cx_i = crossover(indep)
    cx_c = crossover(corr)
    rec_i = cx_i["recommended_max_attempts"]

    # paired: same population, does correlation significantly cut success at K=rec_i?
    pair = mcnemar_from_pairs(S.success_flags(rec_i, "correlated"),
                              S.success_flags(rec_i, "independent"))

    guard = {"independent": fail_condition_check(indep, rec_i),
             "correlated": fail_condition_check(corr, cx_c["recommended_max_attempts"])}

    return {
        "params": {"N": S.N, "KMAX": S.KMAX, "p_flaky": S.P_FLAKY,
                   "rho_persistent": S.RHO_PERSISTENT, "outage_frac": S.OUTAGE_FRAC,
                   "queue_coef": S.QUEUE_COEF, "seed": S.SEED},
        "ceilings": {"cost_ceiling_amplification": COST_CEILING_AMP,
                     "p99_latency_budget": P99_BUDGET,
                     "min_marginal_success": MIN_MARGINAL_SUCCESS},
        "sweep_independent": indep,
        "sweep_correlated": corr,
        "crossover_independent": cx_i,
        "crossover_correlated": cx_c,
        "paired_correlation_effect_at_recommended_K": {"K": rec_i, "mcnemar": pair},
        "fail_condition_guard": guard,
        "q3_conclusion": {
            "recommended_region": {
                "independent_max_attempts": rec_i,
                "correlated_max_attempts": cx_c["recommended_max_attempts"]},
            "crossover_K": {"independent": cx_i["crossover_K"],
                            "correlated": cx_c["crossover_K"]},
            "statement": (
                f"Retries help until roughly K={cx_i['crossover_K']} on independent "
                f"failures, but the DEFENSIBLE budget is K={rec_i} — beyond it, success "
                f"gains fall below {MIN_MARGINAL_SUCCESS} while amplification exceeds "
                f"{COST_CEILING_AMP}x and p99 breaches {P99_BUDGET}. Under CORRELATED "
                f"failures (shared outage + retry storm) retries are near-pure "
                f"amplification: success plateaus around "
                f"{max(p['success_rate'] for p in corr)} while amplification reaches "
                f"{max(p['amplification'] for p in corr)}x and p99 reaches "
                f"{max(p['p99_latency'] for p in corr)} — so the correlated budget is "
                f"only K={cx_c['recommended_max_attempts']}, and a circuit breaker "
                f"(Mission 20) is required. The recommendation is capped by the ceilings, "
                f"so it never trades a success bump for an unacceptable cost/tail cost."),
            "fail_condition_respected": (guard["independent"]["respected"]
                                         and guard["correlated"]["respected"]),
        },
    }
