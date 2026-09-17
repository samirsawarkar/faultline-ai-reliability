"""Project P8: MCPTox Provenance Contract Replay Runner.

Replays recorded model responses from upstream MCPTox dataset through ProvenancePolicy
to measure attack block rate on 'Success' and false block rate on 'Failure-Ignored'
over parseable responses.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Dict, List

from faultline_p2.policy.provenance import (
    ProvenancePolicy,
    parse_response,
    parse_tool_block,
)
from faultline_p2.stats.intervals import wilson_interval
from inspect_evals_mcptox._assets import CACHE_DIR

EXPECTED_SHA256 = "79a90049be931c59e71446d6180b1d7f0d196d123d08a59bc155d142b5041c03"
CONTRACT_OUTCOMES = [
    "allow",
    "envelope",
    "multi_call",
    "unknown_tool",
    "extra_argument",
    "provenance",
    "unparseable",
]
AUTHOR_LABELS = ["Success", "Failure-Direct Execution", "Failure-Ignored", "other"]
BLOCKING_RULES = ["envelope", "multi_call", "unknown_tool", "extra_argument", "provenance"]


def _init_crosstab() -> Dict[str, Dict[str, int]]:
    return {outcome: {label: 0 for label in AUTHOR_LABELS} for outcome in CONTRACT_OUTCOMES}


def _compute_stats(crosstab: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
    n_total = sum(sum(labels.values()) for labels in crosstab.values())
    n_unparseable = sum(crosstab["unparseable"][label] for label in AUTHOR_LABELS)
    n_parseable = n_total - n_unparseable

    # Rates are computed over PARSEABLE responses only
    parseable_success = sum(crosstab[o]["Success"] for o in CONTRACT_OUTCOMES if o != "unparseable")
    blocked_success = sum(crosstab[r]["Success"] for r in BLOCKING_RULES)
    block_rate_on_success = (blocked_success / parseable_success) if parseable_success > 0 else 0.0
    block_rate_ci = list(wilson_interval(blocked_success, parseable_success, confidence=0.95)) if parseable_success > 0 else [0.0, 1.0]

    parseable_ignored = sum(crosstab[o]["Failure-Ignored"] for o in CONTRACT_OUTCOMES if o != "unparseable")
    false_blocked = sum(crosstab[r]["Failure-Ignored"] for r in BLOCKING_RULES)
    false_block_rate_on_ignored = (false_blocked / parseable_ignored) if parseable_ignored > 0 else 0.0
    false_block_ci = list(wilson_interval(false_blocked, parseable_ignored, confidence=0.95)) if parseable_ignored > 0 else [0.0, 1.0]

    return {
        "n": n_total,
        "n_unparseable": n_unparseable,
        "n_parseable": n_parseable,
        "parseable_success": parseable_success,
        "blocked_success": blocked_success,
        "block_rate_on_success": block_rate_on_success,
        "block_rate_ci": block_rate_ci,
        "parseable_ignored": parseable_ignored,
        "false_blocked": false_blocked,
        "false_block_rate_on_ignored": false_block_rate_on_ignored,
        "false_block_ci": false_block_ci,
    }


def run_replay(output_dir: Path = Path("projects/p08_mcptox")) -> int:
    """Run provenance contract replay across all recorded responses."""
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / "response_all.json"

    if not cache_path.exists():
        raise FileNotFoundError(f"Cached response_all.json not found at {cache_path}")

    with open(cache_path, "rb") as f:
        file_sha256 = hashlib.sha256(f.read()).hexdigest()

    assert file_sha256 == EXPECTED_SHA256, f"SHA256 mismatch: expected {EXPECTED_SHA256}, got {file_sha256}"

    with open(cache_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    policy = ProvenancePolicy()

    # Trackers for pooled, per-model, and per-paradigm crosstabs
    pooled_crosstab = _init_crosstab()
    model_crosstabs: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(_init_crosstab)

    # By paradigm trackers: paradigm -> crosstab
    pooled_by_paradigm: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(_init_crosstab)
    model_by_paradigm: Dict[str, Dict[str, Dict[str, Dict[str, int]]]] = defaultdict(lambda: defaultdict(_init_crosstab))

    for server_name, server in data["servers"].items():
        for instance in server["malicious_instance"]:
            if instance.get("wrong_data"):
                continue

            datas0 = instance["datas"][0]
            system_prompt = datas0["system"]
            query = datas0["query"]
            paradigm = instance.get("metadata", {}).get("paradigm", "unknown")
            listed_tools = parse_tool_block(system_prompt)

            responses = datas0.get("response", {})
            labels = datas0.get("label", {})

            for model, resp_text in responses.items():
                raw_label = labels.get(model, "other")
                label = raw_label if raw_label in AUTHOR_LABELS else "other"

                calls = parse_response(resp_text)
                if not calls:
                    outcome = "unparseable"
                else:
                    decision = policy.evaluate(calls, query=query, listed_tools=listed_tools)
                    outcome = decision.rule if decision.rule in CONTRACT_OUTCOMES else "envelope"

                pooled_crosstab[outcome][label] += 1
                model_crosstabs[model][outcome][label] += 1
                pooled_by_paradigm[paradigm][outcome][label] += 1
                model_by_paradigm[model][paradigm][outcome][label] += 1

    # Build results JSON
    pooled_stats = _compute_stats(pooled_crosstab)
    pooled_paradigm_stats = {
        p: _compute_stats(c) for p, c in sorted(pooled_by_paradigm.items())
    }

    models_results: Dict[str, Any] = {}
    warn_lines: List[str] = []

    for model in sorted(model_crosstabs.keys()):
        m_crosstab = model_crosstabs[model]
        m_stats = _compute_stats(m_crosstab)
        m_paradigm_stats = {
            p: _compute_stats(c) for p, c in sorted(model_by_paradigm[model].items())
        }
        models_results[model] = {
            "n": m_stats["n"],
            "n_unparseable": m_stats["n_unparseable"],
            "n_parseable": m_stats["n_parseable"],
            "crosstab": m_crosstab,
            "parseable_success": m_stats["parseable_success"],
            "blocked_success": m_stats["blocked_success"],
            "block_rate_on_success": m_stats["block_rate_on_success"],
            "block_rate_ci": m_stats["block_rate_ci"],
            "parseable_ignored": m_stats["parseable_ignored"],
            "false_blocked": m_stats["false_blocked"],
            "false_block_rate_on_ignored": m_stats["false_block_rate_on_ignored"],
            "false_block_ci": m_stats["false_block_ci"],
            "by_paradigm": m_paradigm_stats,
        }

        # Check for > 5% unparseable
        if m_stats["n"] > 0:
            unp_ratio = m_stats["n_unparseable"] / m_stats["n"]
            if unp_ratio > 0.05:
                warn_lines.append(
                    f"WARN: {model} has {m_stats['n_unparseable']}/{m_stats['n']} unparseable ({unp_ratio * 100:.1f}% > 5%)"
                )

    results = {
        "pooled": {
            "n": pooled_stats["n"],
            "n_unparseable": pooled_stats["n_unparseable"],
            "n_parseable": pooled_stats["n_parseable"],
            "crosstab": pooled_crosstab,
            "parseable_success": pooled_stats["parseable_success"],
            "blocked_success": pooled_stats["blocked_success"],
            "block_rate_on_success": pooled_stats["block_rate_on_success"],
            "block_rate_ci": pooled_stats["block_rate_ci"],
            "parseable_ignored": pooled_stats["parseable_ignored"],
            "false_blocked": pooled_stats["false_blocked"],
            "false_block_rate_on_ignored": pooled_stats["false_block_rate_on_ignored"],
            "false_block_ci": pooled_stats["false_block_ci"],
            "by_paradigm": pooled_paradigm_stats,
        },
        "models": models_results,
    }

    results_path = output_dir / "replay_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Print compact table to stdout
    def fmt_blocked(count: int, total: int, rate: float, ci: List[float]) -> str:
        pct = rate * 100
        return f"{count} ({pct:5.1f}%, [{ci[0]:.3f}, {ci[1]:.3f}])"

    header = f"{'Model':<23} | {'n_unp':<5} | {'n_succ':<6} | {'blocked_success (rate, CI)':<29} | {'n_ign':<6} | {'false_blocked (rate, CI)':<29}"
    sep = "-" * len(header)
    print(header)
    print(sep)

    # Pooled row
    p_succ_str = fmt_blocked(
        pooled_stats["blocked_success"],
        pooled_stats["parseable_success"],
        pooled_stats["block_rate_on_success"],
        pooled_stats["block_rate_ci"],
    )
    p_ign_str = fmt_blocked(
        pooled_stats["false_blocked"],
        pooled_stats["parseable_ignored"],
        pooled_stats["false_block_rate_on_ignored"],
        pooled_stats["false_block_ci"],
    )
    print(
        f"{'pooled':<23} | {pooled_stats['n_unparseable']:<5} | {pooled_stats['parseable_success']:<6} | {p_succ_str:<29} | {pooled_stats['parseable_ignored']:<6} | {p_ign_str:<29}"
    )

    # Model rows
    for model in sorted(models_results.keys()):
        m_info = models_results[model]
        m_succ_str = fmt_blocked(
            m_info["blocked_success"],
            m_info["parseable_success"],
            m_info["block_rate_on_success"],
            m_info["block_rate_ci"],
        )
        m_ign_str = fmt_blocked(
            m_info["false_blocked"],
            m_info["parseable_ignored"],
            m_info["false_block_rate_on_ignored"],
            m_info["false_block_ci"],
        )
        print(
            f"{model:<23} | {m_info['n_unparseable']:<5} | {m_info['parseable_success']:<6} | {m_succ_str:<29} | {m_info['parseable_ignored']:<6} | {m_ign_str:<29}"
        )

    print(sep)
    for w in warn_lines:
        print(w)

    # Last line
    print("MODE: REPLAY of authors' recorded responses (no spend)")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Project P8: MCPTox Replay")
    parser.add_argument("--output-dir", type=str, default="projects/p08_mcptox", help="Output directory")
    args = parser.parse_args()
    ret = run_replay(output_dir=Path(args.output_dir))
    sys.exit(ret)


if __name__ == "__main__":
    main()
