"""Calibrated cascade simulation pure functions.

Deterministic simulation of cheap->frontier model cascades without an LLM judge:
- Evaluates rule-based escalation signals based on R2 runtime trace metadata.
- Optimizes escalation thresholds on a train split and evaluates on a held-out test split.
- Computes Pareto frontiers of (mean_cost, pass_rate).
"""
from __future__ import annotations

import hashlib
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

from faultline_p2.stats.intervals import wilson_interval


def split_scenarios(
    scenario_ids: Sequence[str], train_frac: float = 0.7
) -> Tuple[List[str], List[str]]:
    """Content-addressed deterministic train/test split.

    Hashes each scenario_id using SHA-256 and sorts lexicographically by hex digest.
    The first `int(len(sorted_ids) * train_frac)` items form the train split;
    the remainder form the test split. Disjoint and deterministic across platforms.
    """
    unique_ids = sorted(set(scenario_ids))
    hashed_ids = sorted(
        unique_ids,
        key=lambda sid: hashlib.sha256(sid.encode("utf-8")).hexdigest(),
    )
    n_train = int(len(hashed_ids) * train_frac)
    return hashed_ids[:n_train], hashed_ids[n_train:]


def _get_steps(r2: Dict[str, Any]) -> int:
    """Extract step count from R2 run dict."""
    if "steps_used" in r2 and r2["steps_used"] is not None:
        return int(r2["steps_used"])
    steps = r2.get("steps")
    if isinstance(steps, int):
        return steps
    if isinstance(steps, list):
        return len(steps)
    return 0


def _is_not_answered(r2: Dict[str, Any]) -> bool:
    """True if R2 did not terminate with status == 'answered'."""
    return r2.get("status") != "answered"


def _has_no_citation(r2: Dict[str, Any]) -> bool:
    """True if cited_sources is missing, empty, or None."""
    sources = r2.get("cited_sources")
    return not bool(sources)


# Built-in policy callables
def r2_only(r2: Dict[str, Any]) -> bool:
    """Never escalate to frontier; always accept R2."""
    return False


def r4_only(r2: Dict[str, Any]) -> bool:
    """Always escalate to frontier R4."""
    return True


def escalate_if_not_answered(r2: Dict[str, Any]) -> bool:
    """Escalate if R2 failed to produce an answer (e.g. step_cap, malformed)."""
    return _is_not_answered(r2)


def escalate_if_no_citation(r2: Dict[str, Any]) -> bool:
    """Escalate if R2 cited no sources."""
    return _has_no_citation(r2)


def make_escalate_if_steps_ge_t(t: int) -> Callable[[Dict[str, Any]], bool]:
    """Escalate if R2 consumed >= t steps."""
    return lambda r2: _get_steps(r2) >= t


def make_escalate_if_not_answered_or_steps_ge_t(t: int) -> Callable[[Dict[str, Any]], bool]:
    """Escalate if R2 was not answered OR consumed >= t steps."""
    return lambda r2: _is_not_answered(r2) or (_get_steps(r2) >= t)


def get_policy(name_or_fn: Union[str, Callable[[Dict[str, Any]], bool]]) -> Callable[[Dict[str, Any]], bool]:
    """Resolve a policy by name or return the callable."""
    if callable(name_or_fn):
        return name_or_fn

    name = str(name_or_fn).strip()
    if name == "r2_only":
        return r2_only
    if name == "r4_only":
        return r4_only
    if name == "escalate_if_not_answered":
        return escalate_if_not_answered
    if name == "escalate_if_no_citation":
        return escalate_if_no_citation

    if name.startswith("escalate_if_not_answered_or_steps_ge_"):
        t = int(name.split("_")[-1])
        return make_escalate_if_not_answered_or_steps_ge_t(t)

    if name.startswith("escalate_if_steps_ge_"):
        t = int(name.split("_")[-1])
        return make_escalate_if_steps_ge_t(t)

    raise ValueError(f"Unknown policy name: '{name}'")


def get_all_candidate_policies() -> Dict[str, Callable[[Dict[str, Any]], bool]]:
    """Return dictionary of all candidate policies evaluated in cascade optimization."""
    policies: Dict[str, Callable[[Dict[str, Any]], bool]] = {
        "r2_only": r2_only,
        "r4_only": r4_only,
        "escalate_if_not_answered": escalate_if_not_answered,
        "escalate_if_no_citation": escalate_if_no_citation,
    }
    for t in range(2, 25):
        policies[f"escalate_if_steps_ge_{t}"] = make_escalate_if_steps_ge_t(t)
    for t in range(2, 25):
        policies[f"escalate_if_not_answered_or_steps_ge_{t}"] = make_escalate_if_not_answered_or_steps_ge_t(t)
    return policies


def _extract_pair_components(pair: Dict[str, Any]) -> Tuple[Dict[str, Any], bool, bool, float, float]:
    """Extract (r2_run_dict, r2_grounded, r4_grounded, r2_cost, r4_cost) from pair dict."""
    r2_run = pair.get("r2") if isinstance(pair.get("r2"), dict) else pair
    r4_run = pair.get("r4") if isinstance(pair.get("r4"), dict) else {}

    r2_pass = bool(pair.get("r2_grounded", pair.get("r2_passed", r2_run.get("grounded", False))))
    r4_pass = bool(pair.get("r4_grounded", pair.get("r4_passed", r4_run.get("grounded", False))))

    r2_cost = float(pair.get("r2_cost", r2_run.get("cost_usd", 0.0)))
    r4_cost = float(pair.get("r4_cost", r4_run.get("cost_usd", 0.0)))

    return r2_run, r2_pass, r4_pass, r2_cost, r4_cost


def evaluate(
    policy: Union[str, Callable[[Dict[str, Any]], bool]],
    pairs: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """Evaluate a cascade policy on a set of scenario pairs.

    For each scenario:
      - If policy(r2) is True: escalate to R4. Pass = r4_grounded, Cost = r2_cost + r4_cost.
      - Else: accept R2. Pass = r2_grounded, Cost = r2_cost.

    Returns dict containing pass_rate with Wilson CI, mean_cost, escalation_rate, n.
    """
    pol_fn = get_policy(policy)
    pol_name = policy if isinstance(policy, str) else getattr(policy, "__name__", "custom_policy")

    n = len(pairs)
    if n == 0:
        return {
            "policy": pol_name,
            "n": 0,
            "passed": 0,
            "pass_rate": 0.0,
            "wilson_ci": [0.0, 1.0],
            "mean_cost": 0.0,
            "total_cost": 0.0,
            "escalations": 0,
            "escalation_rate": 0.0,
        }

    passes = 0
    escalations = 0
    total_cost = 0.0

    for pair in pairs:
        r2_run, r2_pass, r4_pass, r2_cost, r4_cost = _extract_pair_components(pair)
        escalate = pol_fn(r2_run)

        if escalate:
            escalations += 1
            scenario_passed = r4_pass
            scenario_cost = r2_cost + r4_cost
        else:
            scenario_passed = r2_pass
            scenario_cost = r2_cost

        if scenario_passed:
            passes += 1
        total_cost += scenario_cost

    pass_rate = passes / n
    ci = wilson_interval(passes, n)
    mean_cost = total_cost / n
    escalation_rate = escalations / n

    return {
        "policy": pol_name,
        "n": n,
        "passed": passes,
        "pass_rate": pass_rate,
        "wilson_ci": [ci[0], ci[1]],
        "mean_cost": mean_cost,
        "total_cost": total_cost,
        "escalations": escalations,
        "escalation_rate": escalation_rate,
    }


def _extract_cost_pass(p: Any) -> Tuple[float, float]:
    """Extract (cost, pass_rate) tuple from point representation."""
    if isinstance(p, dict):
        cost = p.get("mean_cost", p.get("cost", 0.0))
        pass_rate = p.get("pass_rate", p.get("pass", 0.0))
        return float(cost), float(pass_rate)
    if isinstance(p, (tuple, list)):
        return float(p[0]), float(p[1])
    cost = getattr(p, "mean_cost", getattr(p, "cost", 0.0))
    pass_rate = getattr(p, "pass_rate", getattr(p, "pass_rate", 0.0))
    return float(cost), float(pass_rate)


def pareto_frontier(points: Sequence[Any]) -> List[Any]:
    """Find the non-dominated Pareto frontier over (cost low, pass high), sorted by cost.

    Point A dominates Point B iff:
      cost_A <= cost_B AND pass_A >= pass_B AND (cost_A < cost_B OR pass_A > pass_B).
    Returns list of non-dominated items, sorted ascending by cost.
    """
    if not points:
        return []

    non_dominated: List[Any] = []
    for p in points:
        p_cost, p_pass = _extract_cost_pass(p)
        dominated = False
        for other in points:
            o_cost, o_pass = _extract_cost_pass(other)
            if (o_cost <= p_cost and o_pass >= p_pass) and (o_cost < p_cost or o_pass > p_pass):
                dominated = True
                break
        if not dominated:
            non_dominated.append(p)

    non_dominated.sort(key=lambda p: (_extract_cost_pass(p)[0], -_extract_cost_pass(p)[1]))
    return non_dominated


def fit(
    pairs_train: Sequence[Dict[str, Any]],
    pairs_test: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Fit policy thresholds on pairs_train and evaluate on pairs_test.

    For each parameterized policy family, selects threshold t in 2..24 maximizing
    train pass rate (ties broken by lowest mean cost, then lowest t).
    Then evaluates the chosen policies and baseline policies on pairs_test.
    Returns train and test metrics side-by-side.
    """
    # 1. Fit 'escalate_if_steps_ge_t'
    steps_candidates: Dict[int, Dict[str, Any]] = {}
    for t in range(2, 25):
        name = f"escalate_if_steps_ge_{t}"
        steps_candidates[t] = evaluate(name, pairs_train)

    best_t_steps = max(
        range(2, 25),
        key=lambda t: (steps_candidates[t]["pass_rate"], -steps_candidates[t]["mean_cost"], -t),
    )

    # 2. Fit 'escalate_if_not_answered_or_steps_ge_t'
    combo_candidates: Dict[int, Dict[str, Any]] = {}
    for t in range(2, 25):
        name = f"escalate_if_not_answered_or_steps_ge_{t}"
        combo_candidates[t] = evaluate(name, pairs_train)

    best_t_combo = max(
        range(2, 25),
        key=lambda t: (combo_candidates[t]["pass_rate"], -combo_candidates[t]["mean_cost"], -t),
    )

    chosen_thresholds = {
        "escalate_if_steps_ge_t": best_t_steps,
        "escalate_if_not_answered_or_steps_ge_t": best_t_combo,
    }

    chosen_step_policy = f"escalate_if_steps_ge_{best_t_steps}"
    chosen_combo_policy = f"escalate_if_not_answered_or_steps_ge_{best_t_combo}"

    headline_policies = [
        "r2_only",
        "r4_only",
        "escalate_if_not_answered",
        "escalate_if_no_citation",
        chosen_step_policy,
        chosen_combo_policy,
    ]

    all_policies = get_all_candidate_policies()

    train_metrics: Dict[str, Any] = {}
    all_train_metrics: Dict[str, Any] = {}
    for pol_name in headline_policies:
        train_metrics[pol_name] = evaluate(pol_name, pairs_train)
    for pol_name in all_policies:
        all_train_metrics[pol_name] = evaluate(pol_name, pairs_train)

    test_metrics: Dict[str, Any] = {}
    all_test_metrics: Dict[str, Any] = {}
    side_by_side: Dict[str, Any] = {}
    test_frontier: List[Dict[str, Any]] = []

    if pairs_test is not None:
        for pol_name in headline_policies:
            test_metrics[pol_name] = evaluate(pol_name, pairs_test)
        for pol_name in all_policies:
            all_test_metrics[pol_name] = evaluate(pol_name, pairs_test)

        for pol_name in headline_policies:
            side_by_side[pol_name] = {
                "train": train_metrics[pol_name],
                "test": test_metrics[pol_name],
            }

        test_frontier = pareto_frontier(list(all_test_metrics.values()))
    else:
        for pol_name in headline_policies:
            side_by_side[pol_name] = {
                "train": train_metrics[pol_name],
                "test": None,
            }

    return {
        "chosen_thresholds": chosen_thresholds,
        "thresholds": chosen_thresholds,
        "escalate_if_steps_ge_t": best_t_steps,
        "escalate_if_not_answered_or_steps_ge_t": best_t_combo,
        "chosen_step_policy": chosen_step_policy,
        "chosen_combo_policy": chosen_combo_policy,
        "train_metrics": train_metrics,
        "test_metrics": test_metrics,
        "side_by_side": side_by_side,
        "all_train_metrics": all_train_metrics,
        "all_test_metrics": all_test_metrics,
        "test_frontier": test_frontier,
    }
