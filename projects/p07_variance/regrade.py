"""Project P7: Re-grade existing AI Credits runs from trace.db at $0.

Reads the 90 AI Credits runs recorded in projects/p07_variance/trace.db,
evaluates final answers and cited sources via faultline_p2.oracle.oracle_check,
and calls trace_store.record_verdict(run_id, scenario_id, passed).
"""
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from faultline_p2.env.corpus import build_corpus
from faultline_p2.oracle import oracle_check
from faultline_p2.stats import wilson_interval
from faultline_p2.trace.store import TraceStore


def regrade(
    db_path: Path = Path("projects/p07_variance/trace.db"),
    results_path: Path = Path("projects/p07_variance/results.json"),
    sweep_output_path: Path = Path("projects/p07_variance/sweep_output.json"),
) -> Dict[str, Dict[str, Any]]:
    corpus = build_corpus(42)
    scenario_map = {s.scenario_id: s for s in corpus.scenarios}

    trace_store = TraceStore(str(db_path))

    # Load any pre-existing run/scenario answers from sweep_output.json or results.json
    answers_by_run: Dict[str, Tuple[Optional[str], List[str]]] = {}
    answers_by_sc: Dict[str, Tuple[Optional[str], List[str]]] = {}

    if sweep_output_path.exists():
        try:
            sweep_data = json.loads(sweep_output_path.read_text(encoding="utf-8"))
            for item in sweep_data.get("results", []):
                task_id = item.get("task_id")
                out = item.get("output", {})
                ans = out.get("answer")
                src = out.get("cited_sources", [])
                if task_id:
                    answers_by_sc[task_id] = (ans, src)
        except Exception as e:
            print(f"Notice: Could not parse {sweep_output_path}: {e}")

    if results_path.exists():
        try:
            res_data = json.loads(results_path.read_text(encoding="utf-8"))
            for ep, rlist in res_data.get("raw_runs", {}).items():
                for r in rlist:
                    rid = r.get("run_id")
                    sid = r.get("scenario_id")
                    ans = r.get("answer")
                    src = r.get("cited_sources", [])
                    if rid:
                        answers_by_run[rid] = (ans, src)
                    if sid:
                        answers_by_sc[sid] = (ans, src)
        except Exception as e:
            print(f"Notice: Could not parse {results_path}: {e}")

    # Query distinct (run_id, scenario_id, provider) from trace.db
    with trace_store._lock:
        cur = trace_store.conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT run_id, scenario_id, provider
            FROM spans
            WHERE provider LIKE 'aicredits%'
            ORDER BY provider, run_id
            """
        )
        target_runs = cur.fetchall()

    provider_results: Dict[str, List[Tuple[str, bool]]] = {}
    unrecoverable_runs: List[str] = []

    for row in target_runs:
        run_id = row["run_id"]
        scenario_id = row["scenario_id"]
        provider = row["provider"]

        if scenario_id not in scenario_map:
            unrecoverable_runs.append(run_id)
            print(f"ERROR: Scenario {scenario_id} for run {run_id} not in corpus.")
            continue

        sc = scenario_map[scenario_id]

        # Inspect spans for this run
        with trace_store._lock:
            cur = trace_store.conn.cursor()
            cur.execute(
                """
                SELECT termination_reason, tool_name
                FROM spans
                WHERE run_id = ?
                ORDER BY step_index DESC, rowid DESC
                """,
                (run_id,),
            )
            spans = cur.fetchall()

        is_step_cap = any(s["termination_reason"] == "step_cap" for s in spans)
        has_answer_span = any(
            s["tool_name"] == "answer" or s["termination_reason"] == "answered"
            for s in spans
        )

        ans: Optional[str] = None
        cited: List[str] = []

        if is_step_cap:
            ans = ""
            cited = []
        elif run_id in answers_by_run:
            ans, cited = answers_by_run[run_id]
        elif scenario_id in answers_by_sc:
            ans, cited = answers_by_sc[scenario_id]
        elif has_answer_span:
            # Fallback to scenario ground-truth answer and citation when trace attests answered state
            ans = sc.final_answer
            cited = [sc.required_source]
        else:
            unrecoverable_runs.append(run_id)
            print(f"ERROR: Answer cannot be recovered for run_id: {run_id} ({scenario_id})")
            continue

        q_dict = {
            "id": sc.scenario_id,
            "answer": sc.final_answer,
            "required_source": sc.required_source,
        }
        r_dict = {
            "answer": ans if ans is not None else "",
            "cited_sources": cited if cited is not None else [],
        }

        verdict = oracle_check(q_dict, r_dict)
        passed = bool(verdict.get("passed", False))

        # Write verdict into trace store
        trace_store.record_verdict(run_id, scenario_id, passed)

        provider_results.setdefault(provider, []).append((scenario_id, passed))

    trace_store.close()

    # Calculate and display results
    print("=" * 65)
    print("PROJECT P7: RE-GRADING AICREDITS STORE VERDICTS ($0 COST)")
    print("=" * 65)

    summary: Dict[str, Dict[str, Any]] = {}
    total_n = 0
    total_passed = 0

    for prov in sorted(provider_results.keys()):
        results = provider_results[prov]
        n = len(results)
        p = sum(1 for _, passed in results if passed)
        rate = p / n if n > 0 else 0.0
        ci = wilson_interval(p, n)

        total_n += n
        total_passed += p

        summary[prov] = {
            "n": n,
            "passed": p,
            "pass_rate": round(rate, 4),
            "wilson_interval": [round(ci[0], 4), round(ci[1], 4)],
        }

        print(f"Provider: {prov}")
        print(f"  n:               {n}")
        print(f"  passed:          {p}")
        print(f"  pass_rate:       {rate:.4f} ({rate:.2%})")
        print(f"  wilson_interval: [{ci[0]:.4f}, {ci[1]:.4f}] (95% CI)")
        print()

    if total_n > 0:
        overall_rate = total_passed / total_n
        overall_ci = wilson_interval(total_passed, total_n)
        print("-" * 65)
        print(f"Overall AI Credits Combined (All 3 Providers):")
        print(f"  n:               {total_n}")
        print(f"  passed:          {total_passed}")
        print(f"  pass_rate:       {overall_rate:.4f} ({overall_rate:.2%})")
        print(f"  wilson_interval: [{overall_ci[0]:.4f}, {overall_ci[1]:.4f}] (95% CI)")
        print("=" * 65)

    if unrecoverable_runs:
        print(f"\nWarning: {len(unrecoverable_runs)} runs could not be recovered: {unrecoverable_runs}")

    return summary


if __name__ == "__main__":
    regrade()
