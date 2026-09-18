from __future__ import annotations

from typing import Any, Dict, List, Sequence

from faultline_p2.stats.intervals import wilson_interval
from faultline_p2.stats.paired import mcnemar_from_pairs


def is_infra_dead(spans: Sequence[Dict[str, Any]]) -> bool:
    """Detect if a run is infrastructure-dead.
    
    A run is infrastructure-dead iff every span of that run has
    completion_tokens == 0 (or None) AND max(step_index) <= 1.
    """
    if not spans:
        return True
    max_step = max(s.get("step_index", 0) for s in spans)
    all_zero_tokens = all(
        s.get("completion_tokens") is None or s.get("completion_tokens") == 0
        for s in spans
    )
    return max_step <= 1 and all_zero_tokens


def _compute_metrics_block(pairs: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute attribution counts and statistics for a collection of scenario pairs."""
    retriever_owned = sum(1 for p in pairs if not p.get("a_passed", False) and p.get("b_passed", False))
    generator_owned = sum(1 for p in pairs if not p.get("a_passed", False) and not p.get("b_passed", False))
    reverse = sum(1 for p in pairs if p.get("a_passed", False) and not p.get("b_passed", False))
    both_pass = sum(1 for p in pairs if p.get("a_passed", False) and p.get("b_passed", False))
    n_failures_a = retriever_owned + generator_owned

    if n_failures_a > 0:
        retriever_share = retriever_owned / n_failures_a
        ci = wilson_interval(retriever_owned, n_failures_a)
    else:
        retriever_share = 0.0
        ci = (0.0, 1.0)

    # H8: Retrieval owns >50% of grounding failures; falsified if attribution CI excludes 50% on generator side
    if ci[0] > 0.5:
        h8_verdict = "SUPPORTED"
    elif ci[1] < 0.5:
        h8_verdict = "FALSIFIED"
    else:
        h8_verdict = "UNDECIDED"

    a_bools = [bool(p.get("a_passed", False)) for p in pairs]
    b_bools = [bool(p.get("b_passed", False)) for p in pairs]
    mcnemar_block = mcnemar_from_pairs(a_bools, b_bools) if pairs else {}

    # Per-tier breakdown
    tiers = sorted({p["tier"] for p in pairs if "tier" in p})
    per_tier: Dict[str, Any] = {}
    for t in tiers:
        t_pairs = [p for p in pairs if p.get("tier") == t]
        t_retriever_owned = sum(1 for p in t_pairs if not p.get("a_passed", False) and p.get("b_passed", False))
        t_generator_owned = sum(1 for p in t_pairs if not p.get("a_passed", False) and not p.get("b_passed", False))
        t_reverse = sum(1 for p in t_pairs if p.get("a_passed", False) and not p.get("b_passed", False))
        t_both_pass = sum(1 for p in t_pairs if p.get("a_passed", False) and p.get("b_passed", False))
        t_n_fail_a = t_retriever_owned + t_generator_owned
        t_share = (t_retriever_owned / t_n_fail_a) if t_n_fail_a > 0 else 0.0
        t_ci = wilson_interval(t_retriever_owned, t_n_fail_a) if t_n_fail_a > 0 else (0.0, 1.0)
        t_verdict = "SUPPORTED" if t_ci[0] > 0.5 else ("FALSIFIED" if t_ci[1] < 0.5 else "UNDECIDED")
        per_tier[t] = {
            "counts": {
                "retriever_owned": t_retriever_owned,
                "generator_owned": t_generator_owned,
                "reverse": t_reverse,
                "both_pass": t_both_pass,
                "n_failures_a": t_n_fail_a,
                "total_pairs": len(t_pairs),
            },
            "retriever_owned": t_retriever_owned,
            "generator_owned": t_generator_owned,
            "reverse": t_reverse,
            "both_pass": t_both_pass,
            "n_failures_a": t_n_fail_a,
            "retriever_share": t_share,
            "wilson_ci": [t_ci[0], t_ci[1]],
            "h8_verdict": t_verdict,
            "total_pairs": len(t_pairs),
        }

    # Per-a_status breakdown of the failures
    failures_a = [p for p in pairs if not p.get("a_passed", False)]
    statuses = sorted({str(p["a_status"]) for p in failures_a if p.get("a_status") is not None})
    per_a_status: Dict[str, Any] = {}
    for st in statuses:
        st_pairs = [p for p in failures_a if str(p.get("a_status")) == st]
        st_retriever_owned = sum(1 for p in st_pairs if p.get("b_passed", False))
        st_generator_owned = sum(1 for p in st_pairs if not p.get("b_passed", False))
        st_count = len(st_pairs)
        st_share = (st_retriever_owned / st_count) if st_count > 0 else 0.0
        st_ci = wilson_interval(st_retriever_owned, st_count) if st_count > 0 else (0.0, 1.0)
        per_a_status[st] = {
            "count": st_count,
            "retriever_owned": st_retriever_owned,
            "generator_owned": st_generator_owned,
            "retriever_share": st_share,
            "wilson_ci": [st_ci[0], st_ci[1]],
        }

    counts = {
        "retriever_owned": retriever_owned,
        "generator_owned": generator_owned,
        "reverse": reverse,
        "both_pass": both_pass,
        "n_failures_a": n_failures_a,
        "total_pairs": len(pairs),
    }

    return {
        "counts": counts,
        "retriever_owned": retriever_owned,
        "generator_owned": generator_owned,
        "reverse": reverse,
        "both_pass": both_pass,
        "n_failures_a": n_failures_a,
        "retriever_share": retriever_share,
        "wilson_ci": [ci[0], ci[1]],
        "h8_verdict": h8_verdict,
        "mcnemar": mcnemar_block,
        "per_tier": per_tier,
        "per_a_status": per_a_status,
        "total_pairs": len(pairs),
    }


def attribute(pairs: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Perform failure attribution across matched Arm A and Arm B scenarios.
    
    Computes twice:
    - as_run: all pairs
    - infra_excluded: drops pairs where either arm is infra_dead
    """
    as_run = _compute_metrics_block(pairs)

    infra_excluded_pairs = [
        p for p in pairs
        if not (bool(p.get("a_infra_dead", False)) or bool(p.get("b_infra_dead", False)))
    ]
    infra_excluded = _compute_metrics_block(infra_excluded_pairs)

    return {
        "as_run": as_run,
        "infra_excluded": infra_excluded,
        "retriever_owned": as_run["retriever_owned"],
        "generator_owned": as_run["generator_owned"],
        "reverse": as_run["reverse"],
        "both_pass": as_run["both_pass"],
        "n_failures_a": as_run["n_failures_a"],
        "retriever_share": as_run["retriever_share"],
        "wilson_ci": as_run["wilson_ci"],
        "h8_verdict": as_run["h8_verdict"],
        "mcnemar": as_run["mcnemar"],
        "per_tier": as_run["per_tier"],
        "per_a_status": as_run["per_a_status"],
        "counts": as_run["counts"],
    }


def analyze_retrieval_mechanism(
    pairs: Sequence[Dict[str, Any]],
    traces_a: Dict[str, Any],
    scenario_traversal_sources: Dict[str, Sequence[str]],
) -> Dict[str, Any]:
    """Analyze retrieval failure mechanism across matched scenario pairs.

    For each retriever-owned failure:
      - Reads Arm A trace
      - Collects every doc_id in any search observation's candidates
      - Compares with scenario traversal_sources
      - Reports never_surfaced (>=1 needed doc never returned by search)
        vs surfaced_but_unused (all needed docs returned yet run failed)
      - Computes histogram of missing-doc counts
    Also reports Arm A failure status counts split by retriever/generator owned.
    """
    never_surfaced = 0
    surfaced_but_unused = 0
    missing_histogram: Dict[int, int] = {}
    retr_status: Dict[str, int] = {}
    gen_status: Dict[str, int] = {}

    for p in pairs:
        sid = p.get("scenario_id", "")
        a_passed = bool(p.get("a_passed", False))
        b_passed = bool(p.get("b_passed", False))
        a_status = str(p.get("a_status", "unknown"))

        if not a_passed and b_passed:
            retr_status[a_status] = retr_status.get(a_status, 0) + 1
            needed_docs = set(scenario_traversal_sources.get(sid, []))

            a_data = traces_a.get(sid, [])
            if isinstance(a_data, dict):
                trace = a_data.get("trace") or a_data.get("steps") or []
            else:
                trace = a_data

            surfaced_docs = set()
            for step in trace:
                if isinstance(step, dict):
                    obs = step.get("observation")
                    if isinstance(obs, dict):
                        candidates = obs.get("candidates") or []
                        for c in candidates:
                            if isinstance(c, dict) and "doc_id" in c:
                                surfaced_docs.add(c["doc_id"])

            missing = needed_docs - surfaced_docs
            n_missing = len(missing)
            missing_histogram[n_missing] = missing_histogram.get(n_missing, 0) + 1
            if n_missing > 0:
                never_surfaced += 1
            else:
                surfaced_but_unused += 1

        elif not a_passed and not b_passed:
            gen_status[a_status] = gen_status.get(a_status, 0) + 1

    return {
        "never_surfaced": never_surfaced,
        "surfaced_but_unused": surfaced_but_unused,
        "missing_doc_histogram": {str(k): v for k, v in sorted(missing_histogram.items())},
        "status_split": {
            "retriever_owned": retr_status,
            "generator_owned": gen_status,
        },
    }
