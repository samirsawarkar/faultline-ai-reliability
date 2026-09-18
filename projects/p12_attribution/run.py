"""Project P12: Failure Attribution & Oracle Retrieval Benchmark.

Evaluates Pre-Registered Hypothesis H8:
'Retrieval owns >50% of grounding failures; falsified if the attribution CI excludes 50% on the generator side'

Compares Arm A (normal agent) vs Arm B (oracle retrieval surfacing traversal_sources) on matched scenarios.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import logging
import os
import sqlite3
import sys
import threading
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from dotenv import load_dotenv

warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("LiteLLM").setLevel(logging.ERROR)

from faultline_p2.agent.agent import run_agent
from faultline_p2.agent.contracts import OutcomeStatus, ScenarioTask
from faultline_p2.agent.model import LiteLLMModel, ModelInterface, ModelResponse, StubModel
from faultline_p2.attribute.attribution import analyze_retrieval_mechanism, attribute
from faultline_p2.attribute.oracle_toolbox import OracleToolBox
from faultline_p2.cost.ledger import CostLedger, LedgerEntry, PriceTable, RungPricing
from faultline_p2.env.corpus import Scenario, build_corpus
from faultline_p2.oracle._day01_oracle import oracle_check
from faultline_p2.resilience import CircuitBreaker, ResilientModel, RetryPolicy
from faultline_p2.sweep.runner import SweepRunner
from faultline_p2.trace.store import TraceStore

DEFAULT_AICREDITS_BASE = "https://aicredits.in/v1"

RUNG_CONFIG: Dict[str, Dict[str, Any]] = {
    "R2": {
        "rung": "R2",
        "role": "Cheap Workhorse",
        "model_name": os.getenv("MODEL_R2", "z-ai/glm-5.3-flash"),
        "provider": "aicredits",
        "version": "glm-5.3-flash",
        "in_price": 0.14,
        "out_price": 0.28,
        # P6-measured final-pass per-run tokens from projects/p06_passk/results.json (rungs.R2.tokens / total_runs)
        "est_in_tokens": 59452,
        "est_out_tokens": 3364,
    },
    "R4": {
        "rung": "R4",
        "role": "OpenAI Frontier",
        "model_name": os.getenv("MODEL_R4", "openai/gpt-5.6-luna"),
        "provider": "aicredits",
        "version": "gpt-5.6-luna",
        "in_price": 0.60,
        "out_price": 2.40,
        # P6-measured final-pass per-run tokens from projects/p06_passk/results.json (rungs.R4.tokens / total_runs)
        "est_in_tokens": 55002,
        "est_out_tokens": 2891,
    },
}


class TrackedLiteLLMModel:
    """Wraps LiteLLMModel to capture the actual response.model attribute returned by LiteLLM."""
    def __init__(self, inner: LiteLLMModel):
        self.inner = inner
        self.model_name = inner.model_name
        self.provider = inner.provider
        self.version = inner.version
        self.reported_model: Optional[str] = None

    def generate(self, messages: List[Dict[str, Any]]) -> ModelResponse:
        import litellm
        reported = [None]
        orig_completion = litellm.completion

        def _completion_wrapper(*args, **kwargs):
            resp = orig_completion(*args, **kwargs)
            reported[0] = getattr(resp, "model", None)
            return resp

        litellm.completion = _completion_wrapper
        try:
            res = self.inner.generate(messages)
        finally:
            litellm.completion = orig_completion

        if reported[0]:
            self.reported_model = str(reported[0])
            self.version = self.reported_model
        return res


def make_model(rung_cfg: Dict[str, Any], stub: bool = False) -> ModelInterface:
    if stub:
        return StubModel(behavior="solver")

    aicredits_key = os.getenv("AICREDITS_API_KEY")
    aicredits_base = os.getenv("AICREDITS_BASE_URL", DEFAULT_AICREDITS_BASE)
    raw_model = LiteLLMModel(
        model_name=rung_cfg["model_name"],
        provider=rung_cfg["provider"],
        version=rung_cfg["version"],
        dry_run=False,
        api_base=aicredits_base,
        api_key=aicredits_key,
        custom_llm_provider="openai",
    )
    tracked_model = TrackedLiteLLMModel(raw_model)
    retry_policy = RetryPolicy(
        max_retries=5,
        initial_backoff_s=2.0,
        backoff_multiplier=2.0,
        max_backoff_s=30.0,
        seed=42,
    )
    return ResilientModel(
        inner_model=tracked_model,
        retry_policy=retry_policy,
        circuit_breaker=CircuitBreaker(failure_threshold=5, cooldown_seconds=5.0),
    )


def select_scenarios(corpus: Any, pool: str, scenario_count: int) -> List[str]:
    if pool == "hard":
        reserved = [s for s in corpus.scenarios if s.pool == "reserved"]
        return [s.scenario_id for s in reserved[:scenario_count]]
    elif pool == "mixed":
        t1 = [s for s in corpus.scenarios if s.tier == "T1"]
        t2 = [s for s in corpus.scenarios if s.tier == "T2"]
        t3 = [s for s in corpus.scenarios if s.tier == "T3"]
        per_tier = scenario_count // 3
        rem = scenario_count % 3
        n_t1 = per_tier + (1 if rem > 0 else 0)
        n_t2 = per_tier + (1 if rem > 1 else 0)
        n_t3 = per_tier
        return (
            [s.scenario_id for s in t1[:n_t1]]
            + [s.scenario_id for s in t2[:n_t2]]
            + [s.scenario_id for s in t3[:n_t3]]
        )
    else:
        raise ValueError(f"Unknown pool type: {pool}")


def ensure_manifest(
    output_dir: Path,
    corpus: Any,
    selected_ids: List[str],
    rung: str,
    pool: str,
) -> Dict[str, Any]:
    manifest_path = output_dir / f"manifest_{rung}.json"
    scenario_map = {s.scenario_id: s for s in corpus.scenarios}
    sampled = [scenario_map[sid] for sid in selected_ids if sid in scenario_map]

    manifest_data = {
        "spec_version": "2.0.0",
        "experiment": "p12_attribution",
        "hypothesis": "H8: Retrieval owns >50% of grounding failures; falsified if attribution CI excludes 50% on generator side",
        "rung": rung,
        "pool": pool,
        "corpus_hash": corpus.content_hash,
        "scenario_count": len(selected_ids),
        "tier_counts": {
            "T1": sum(1 for s in sampled if s.tier == "T1"),
            "T2": sum(1 for s in sampled if s.tier == "T2"),
            "T3": sum(1 for s in sampled if s.tier == "T3"),
        },
        "scenario_ids_sha256": hashlib.sha256(json.dumps(selected_ids).encode()).hexdigest(),
        "scenario_ids": selected_ids,
    }
    manifest_bytes = json.dumps(manifest_data, indent=2, sort_keys=True).encode()
    manifest_data["manifest_sha256"] = hashlib.sha256(manifest_bytes).hexdigest()

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    return manifest_data


def check_run_infra_dead(trace_db_path: Path, run_id: str) -> bool:
    if not trace_db_path.exists():
        return False
    try:
        conn = sqlite3.connect(str(trace_db_path))
        cur = conn.cursor()
        cur.execute("SELECT step_index, completion_tokens FROM spans WHERE run_id = ?", (run_id,))
        rows = cur.fetchall()
        conn.close()
        if not rows:
            return False
        max_step = max(r[0] for r in rows)
        all_zero_tokens = all(r[1] is None or r[1] == 0 for r in rows)
        return max_step <= 1 and all_zero_tokens
    except Exception:
        return False


def execute_scenario(
    task: ScenarioTask,
    scenario: Scenario,
    corpus: Any,
    arm: str,
    rung: str,
    rung_cfg: Dict[str, Any],
    trace_store: TraceStore,
    ledger: CostLedger,
    step_cap: int,
    stub: bool,
    run_id: str,
    model: ModelInterface,
    project: str = "p12_attribution",
) -> Dict[str, Any]:
    env = {"documents": corpus.documents}

    if arm == "B":
        toolbox = OracleToolBox(env=env, traversal_sources=scenario.traversal_sources)
    else:
        toolbox = None

    t_start = time.time()
    outcome = run_agent(
        task=task,
        env=env,
        model=model,
        step_cap=step_cap,
        trace_store=trace_store,
        run_id=run_id,
        toolbox=toolbox,
    )
    wall_ms = (time.time() - t_start) * 1000

    q_dict = {
        "id": scenario.scenario_id,
        "answer": scenario.final_answer,
        "required_source": scenario.required_source,
    }
    r_dict = {
        "answer": outcome.answer or "",
        "cited_sources": outcome.cited_sources,
    }
    verdict = oracle_check(q_dict, r_dict)
    passed = bool(verdict.get("passed", False))
    trace_store.record_verdict(run_id, scenario.scenario_id, passed)

    reported_model = None
    if hasattr(model, "reported_model") and model.reported_model:
        reported_model = model.reported_model
    elif hasattr(model, "inner_model") and hasattr(model.inner_model, "reported_model") and model.inner_model.reported_model:
        reported_model = model.inner_model.reported_model
    elif stub:
        reported_model = getattr(model, "model_name", "stub")

    if reported_model:
        with trace_store._lock:
            trace_store.conn.execute(
                "UPDATE spans SET model_version = ? WHERE run_id = ?",
                (reported_model, run_id),
            )

    with trace_store._lock:
        cur = trace_store.conn.cursor()
        cur.execute(
            "SELECT SUM(prompt_tokens), SUM(completion_tokens), AVG(latency_ms) FROM spans WHERE run_id = ?",
            (run_id,),
        )
        row = cur.fetchone()
        in_tok = int(row[0] or 0) if row else 0
        out_tok = int(row[1] or 0) if row else 0
        avg_lat = float(row[2] or wall_ms) if row else wall_ms

    cost_usd = (in_tok * rung_cfg["in_price"] / 1e6) + (out_tok * rung_cfg["out_price"] / 1e6)

    if not stub:
        ledger.record(
            LedgerEntry(
                run_id=run_id,
                project=project,
                rung=rung,
                input_tokens=in_tok,
                output_tokens=out_tok,
                usd=cost_usd,
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
            )
        )

    outcome_dict = outcome.model_dump()
    outcome_dict["steps"] = outcome_dict["trace"]  # convenience alias
    outcome_dict["scenario_id"] = scenario.scenario_id
    outcome_dict["run_id"] = run_id
    outcome_dict["tier"] = scenario.tier
    outcome_dict["grounded"] = passed
    outcome_dict["correct_answer"] = verdict.get("correct", False)
    outcome_dict["cited_required"] = verdict.get("cited_required", False)
    outcome_dict["wall_time_ms"] = wall_ms
    outcome_dict["input_tokens"] = in_tok
    outcome_dict["output_tokens"] = out_tok
    outcome_dict["cost_usd"] = cost_usd

    return outcome_dict


def save_sweep_output_incremental(
    sweep_file: Path,
    outcome_dict: Dict[str, Any],
    lock: threading.Lock,
    selected_ids: List[str],
) -> None:
    with lock:
        existing_items: Dict[str, Any] = {}
        if sweep_file.exists():
            try:
                prev = json.loads(sweep_file.read_text(encoding="utf-8"))
                if isinstance(prev, list):
                    for item in prev:
                        sid = item.get("scenario_id") or item.get("task_id")
                        if sid:
                            existing_items[sid] = item
                elif isinstance(prev, dict):
                    existing_items = prev
            except Exception:
                pass
        existing_items[outcome_dict["scenario_id"]] = outcome_dict
        ordered = [existing_items[sid] for sid in selected_ids if sid in existing_items]
        sweep_file.write_text(json.dumps(ordered, indent=2), encoding="utf-8")


def compute_arm_means(trace_db_path: Path, rung: str) -> Dict[str, Dict[str, float]]:
    means: Dict[str, Dict[str, float]] = {}
    if not trace_db_path.exists():
        return means
    try:
        conn = sqlite3.connect(str(trace_db_path))
        for arm in ["A", "B"]:
            prefix = f"{rung}-{arm}-%"
            rows = conn.execute(
                """
                SELECT count(*), sum(prompt_tokens), sum(completion_tokens)
                FROM spans
                WHERE run_id LIKE ?
                GROUP BY run_id
                """,
                (prefix,),
            ).fetchall()
            if rows:
                n = len(rows)
                means[arm] = {
                    "mean_spans": round(sum(r[0] for r in rows) / n, 2),
                    "mean_prompt_tokens": round(sum((r[1] or 0) for r in rows) / n, 1),
                    "mean_completion_tokens": round(sum((r[2] or 0) for r in rows) / n, 1),
                    "mean_total_tokens": round(sum(((r[1] or 0) + (r[2] or 0)) for r in rows) / n, 1),
                }
        conn.close()
    except Exception:
        pass
    return means


def compile_results(
    output_dir: Path,
    rung: str,
    selected_ids: List[str],
    step_cap: int,
    ledger: CostLedger,
    manifest: Dict[str, Any],
    start_utc: str,
    project: str = "p12_attribution",
) -> Dict[str, Any]:
    sweep_a_path = output_dir / f"sweep_output_{rung}_A.json"
    sweep_b_path = output_dir / f"sweep_output_{rung}_B.json"
    trace_db_path = output_dir / "trace.db"

    outcomes_a: Dict[str, Any] = {}
    if sweep_a_path.exists():
        try:
            data_a = json.loads(sweep_a_path.read_text(encoding="utf-8"))
            if isinstance(data_a, list):
                outcomes_a = {r["scenario_id"]: r for r in data_a}
            elif isinstance(data_a, dict):
                outcomes_a = data_a
        except Exception:
            pass

    outcomes_b: Dict[str, Any] = {}
    if sweep_b_path.exists():
        try:
            data_b = json.loads(sweep_b_path.read_text(encoding="utf-8"))
            if isinstance(data_b, list):
                outcomes_b = {r["scenario_id"]: r for r in data_b}
            elif isinstance(data_b, dict):
                outcomes_b = data_b
        except Exception:
            pass

    corpus = build_corpus()
    scenario_map = {s.scenario_id: s for s in corpus.scenarios}

    pairs: List[Dict[str, Any]] = []
    for sid in selected_ids:
        sc = scenario_map.get(sid)
        tier = sc.tier if sc else "unknown"
        oa = outcomes_a.get(sid, {})
        ob = outcomes_b.get(sid, {})

        a_run_id = f"{rung}-A-{sid}"
        b_run_id = f"{rung}-B-{sid}"
        a_infra_dead = check_run_infra_dead(trace_db_path, a_run_id)
        b_infra_dead = check_run_infra_dead(trace_db_path, b_run_id)

        pairs.append({
            "scenario_id": sid,
            "tier": tier,
            "a_passed": bool(oa.get("grounded", False)),
            "b_passed": bool(ob.get("grounded", False)),
            "a_status": oa.get("status", "unknown"),
            "b_status": ob.get("status", "unknown"),
            "a_infra_dead": a_infra_dead,
            "b_infra_dead": b_infra_dead,
        })

    attr_res = attribute(pairs)
    
    rung_spend = 0.0
    if ledger.ledger_path.exists():
        for entry in ledger.read_entries(project=project):
            if entry.rung == rung:
                rung_spend += entry.usd
    spend_usd = round(rung_spend, 4) if rung_spend > 0 else round(ledger.spent(project), 4)

    mechanism = analyze_retrieval_mechanism(
        pairs=pairs,
        traces_a=outcomes_a,
        scenario_traversal_sources={s.scenario_id: s.traversal_sources for s in corpus.scenarios},
    )
    mechanism["arm_means"] = compute_arm_means(trace_db_path, rung)

    end_utc = datetime.now(timezone.utc).isoformat()

    results_data = {
        "spec_version": "2.0.0",
        "experiment": project,
        "hypothesis": "H8: Retrieval owns >50% of grounding failures; falsified if attribution CI excludes 50% on generator side",
        "rung": rung,
        "n": len(selected_ids),
        "step_cap": step_cap,
        "spend_usd": spend_usd,
        "timestamps": {
            "start_utc": start_utc,
            "end_utc": end_utc,
        },
        "metadata": {
            "rung": rung,
            "n": len(selected_ids),
            "step_cap": step_cap,
            "spend_usd": spend_usd,
            "timestamps": {
                "start_utc": start_utc,
                "end_utc": end_utc,
            },
        },
        "h8_verdict": attr_res["as_run"]["h8_verdict"],
        "as_run": attr_res["as_run"],
        "infra_excluded": attr_res["infra_excluded"],
        "mechanism": mechanism,
        "manifest_sha256": manifest.get("manifest_sha256", ""),
    }

    results_path = output_dir / f"results_{rung}.json"
    results_path.write_text(json.dumps(results_data, indent=2), encoding="utf-8")
    return results_data


def run_experiment(
    rung: str = "R2",
    arms: str = "A,B",
    scenarios: int = 150,
    pool: str = "hard",
    step_cap: int = 24,
    concurrency: int = 4,
    dry_run: bool = False,
    confirm: bool = False,
    stub: bool = False,
    recompile: bool = False,
    output_dir_str: str = "projects/p12_attribution",
    project: str = "p12_attribution",
) -> Dict[str, Any]:
    load_dotenv()
    start_utc = datetime.now(timezone.utc).isoformat()
    output_dir = Path(output_dir_str)
    output_dir.mkdir(parents=True, exist_ok=True)

    corpus = build_corpus()
    scenario_map = {s.scenario_id: s for s in corpus.scenarios}

    ledger_path = output_dir / "ledger.jsonl"
    price_table = PriceTable(
        rungs={
            k: RungPricing(
                model_name=v["model_name"],
                input_price_per_m=v["in_price"],
                output_price_per_m=v["out_price"],
            )
            for k, v in RUNG_CONFIG.items()
        }
    )
    ledger = CostLedger(ledger_path=ledger_path)

    arm_list = [a.strip().upper() for a in arms.split(",") if a.strip()]

    # If --recompile, rebuild results directly without executing runs
    if recompile:
        manifest_path = output_dir / f"manifest_{rung}.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            selected_ids = manifest.get("scenario_ids", [])
        else:
            selected_ids = select_scenarios(corpus, pool=pool, scenario_count=scenarios)
            manifest = ensure_manifest(output_dir, corpus, selected_ids, rung=rung, pool=pool)

        res = compile_results(
            output_dir=output_dir,
            rung=rung,
            selected_ids=selected_ids,
            step_cap=step_cap,
            ledger=ledger,
            manifest=manifest,
            start_utc=start_utc,
            project=project,
        )
        print(f"Recompiled results to {output_dir / f'results_{rung}.json'}")
        return res

    # Manifest and scenario selection
    selected_ids = select_scenarios(corpus, pool=pool, scenario_count=scenarios)
    manifest = ensure_manifest(output_dir, corpus, selected_ids, rung=rung, pool=pool)

    rung_cfg = RUNG_CONFIG[rung]
    # Dry-run cost estimate via SweepRunner using P6-measured tokens
    est_in_tokens_per_run = int(rung_cfg["est_in_tokens"] * (step_cap / 24))
    est_out_tokens_per_run = int(rung_cfg["est_out_tokens"] * (step_cap / 24))
    total_runs = len(selected_ids) * len(arm_list)

    runner = SweepRunner(
        project=project,
        price_table=price_table,
        ledger=ledger,
        confirmed=confirm,
    )
    est_cost = runner.dry_run(
        n_runs=total_runs,
        in_tokens=est_in_tokens_per_run,
        out_tokens=est_out_tokens_per_run,
        rung=rung,
    )

    if dry_run or (not confirm and not stub):
        print("\nDry run completed successfully without network spend.")
        return {"dry_run_est_cost_usd": est_cost, "manifest": manifest}

    # If stub mode, ensure ledger file remains empty
    if stub and not ledger_path.exists():
        ledger_path.touch()

    trace_db_path = output_dir / "trace.db"
    trace_store = TraceStore(str(trace_db_path))

    rung_cfg = RUNG_CONFIG[rung]
    save_lock = threading.Lock()

    print(f"\nStarting P12 Sweep: rung={rung}, arms={arm_list}, scenarios={len(selected_ids)}, pool={pool}, stub={stub}")

    for arm in arm_list:
        print(f"\n>>> Executing Arm {arm} ({'Oracle' if arm == 'B' else 'Normal'}) for {len(selected_ids)} scenarios...")
        sweep_file = output_dir / f"sweep_output_{rung}_{arm}.json"
        
        # Load existing runs to allow resuming
        existing_runs: Dict[str, Any] = {}
        if sweep_file.exists():
            try:
                prev_data = json.loads(sweep_file.read_text(encoding="utf-8"))
                if isinstance(prev_data, list):
                    for item in prev_data:
                        sid = item.get("scenario_id") or item.get("task_id")
                        if sid:
                            existing_runs[sid] = item
                elif isinstance(prev_data, dict):
                    existing_runs = prev_data
            except Exception:
                existing_runs = {}

        tasks_to_run = [
            sid for sid in selected_ids if sid not in existing_runs
        ]

        def _worker(sid: str) -> Dict[str, Any]:
            sc = scenario_map[sid]
            task = ScenarioTask(task_id=sid, prompt=sc.prompt, tier=sc.tier)
            run_id = f"{rung}-{arm}-{sid}"
            model = make_model(rung_cfg, stub=stub)
            outcome_dict = execute_scenario(
                task=task,
                scenario=sc,
                corpus=corpus,
                arm=arm,
                rung=rung,
                rung_cfg=rung_cfg,
                trace_store=trace_store,
                ledger=ledger,
                step_cap=step_cap,
                stub=stub,
                run_id=run_id,
                model=model,
                project=project,
            )
            save_sweep_output_incremental(
                sweep_file=sweep_file,
                outcome_dict=outcome_dict,
                lock=save_lock,
                selected_ids=selected_ids,
            )
            status_icon = "PASS" if outcome_dict["grounded"] else "FAIL"
            print(f"  [{rung}-{arm}] {sid} ({sc.tier}) -> {status_icon} (steps={outcome_dict['steps_used']})")
            return outcome_dict

        effective_workers = concurrency if (concurrency > 1 and not stub) else 1
        if effective_workers > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=effective_workers) as pool_exec:
                futures = [pool_exec.submit(_worker, sid) for sid in tasks_to_run]
                for fut in concurrent.futures.as_completed(futures):
                    fut.result()
        else:
            for sid in tasks_to_run:
                _worker(sid)

    # Compile final results
    results = compile_results(
        output_dir=output_dir,
        rung=rung,
        selected_ids=selected_ids,
        step_cap=step_cap,
        ledger=ledger,
        manifest=manifest,
        start_utc=start_utc,
        project=project,
    )

    as_run = results["as_run"]
    counts = as_run["counts"]
    ci = as_run["wilson_ci"]

    print("\n" + "=" * 60)
    print(f"P12 Attribution Summary (Rung {rung}, N={len(selected_ids)}):")
    print(f"  Retriever Owned: {counts['retriever_owned']}")
    print(f"  Generator Owned: {counts['generator_owned']}")
    print(f"  Reverse:         {counts['reverse']}")
    print(f"  Both Pass:       {counts['both_pass']}")
    print(f"  Failures Arm A:  {counts['n_failures_a']}")
    print(f"  Retriever Share: {as_run['retriever_share']:.4f} [95% CI: {ci[0]:.4f}, {ci[1]:.4f}]")
    print(f"  H8 Verdict:      {results['h8_verdict']}")
    print("=" * 60)
    print(f"Results written to {output_dir / f'results_{rung}.json'}")

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="P12: Failure Attribution Runner")
    parser.add_argument("--rung", type=str, default="R2", choices=["R2", "R4"], help="Model rung to evaluate (R2|R4)")
    parser.add_argument("--arms", type=str, default="A,B", help="Arms to evaluate, comma-separated (default: A,B)")
    parser.add_argument("--scenarios", type=int, default=150, help="Number of scenarios (default: 150)")
    parser.add_argument("--pool", type=str, default="hard", choices=["hard", "mixed"], help="Scenario pool (hard|mixed)")
    parser.add_argument("--step-cap", type=int, default=24, help="Step cap per scenario (default: 24)")
    parser.add_argument("--concurrency", type=int, default=4, help="Worker concurrency (default: 4)")
    parser.add_argument("--dry-run", action="store_true", help="Print cost estimate and exit")
    parser.add_argument("--confirm", action="store_true", help="Confirm real LLM spend")
    parser.add_argument("--stub", action="store_true", help="Run with StubModel solver at $0")
    parser.add_argument("--recompile", action="store_true", help="Recompile results_{rung}.json from sweep_output and trace.db")
    parser.add_argument("--output-dir", type=str, default="projects/p12_attribution", help="Output directory")
    parser.add_argument("--project", type=str, default="p12_attribution", help="Project identifier for cost ledger billing")

    args = parser.parse_args()

    run_experiment(
        rung=args.rung,
        arms=args.arms,
        scenarios=args.scenarios,
        pool=args.pool,
        step_cap=args.step_cap,
        concurrency=args.concurrency,
        dry_run=args.dry_run,
        confirm=args.confirm,
        stub=args.stub,
        recompile=args.recompile,
        output_dir_str=args.output_dir,
        project=args.project,
    )


if __name__ == "__main__":
    main()
