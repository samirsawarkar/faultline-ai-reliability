"""Release Gate runner for candidate models against tolerance band.

CLI Arguments:
  --model: <rung|stub:<behaviour>> (e.g. 'R2', 'stub:solver', 'stub:wrong_answer')
  --golden: golden.json path
  --band: band.json or band_stub.json path
  --step-cap: max steps per scenario (default: 24)
  --dry-run: print cost estimate and budget status, exit 0
  --confirm: required to execute paid live model runs
  --report: destination for report.json
  --output-dir: output directory (default: projects/p11_release_gate)
"""
from __future__ import annotations

import argparse
import concurrent.futures
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from faultline_p2.agent.agent import run_agent
from faultline_p2.agent.contracts import ScenarioTask
from faultline_p2.agent.model import LiteLLMModel, ModelInterface, ModelResponse, StubModel
from faultline_p2.config import AICREDITS_BASE_URL, MODEL_LADDER
from faultline_p2.cost.ledger import CostLedger, LedgerEntry, PriceTable, RungPricing
from faultline_p2.env.corpus import Scenario, build_corpus
from faultline_p2.gate.gate import evaluate
from faultline_p2.oracle._day01_oracle import oracle_check
from faultline_p2.resilience import CircuitBreaker, ResilientModel, RetryPolicy
from faultline_p2.sweep.runner import SweepRunner
from faultline_p2.trace.store import TraceStore

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def resolve_path(path_str: str, base_dir: Path) -> Path:
    p = Path(path_str)
    if p.is_file():
        return p
    if (base_dir / path_str).is_file():
        return base_dir / path_str
    if (REPO_ROOT / path_str).is_file():
        return REPO_ROOT / path_str
    return p


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
        orig_completion = litellm.completion

        def _completion_wrapper(*args, **kwargs):
            resp = orig_completion(*args, **kwargs)
            self.reported_model = getattr(resp, "model", None)
            return resp

        litellm.completion = _completion_wrapper
        try:
            return self.inner.generate(messages)
        finally:
            litellm.completion = orig_completion


def make_model(
    model_arg: str,
    golden_scenarios: List[Scenario],
) -> tuple[ModelInterface, Dict[str, Any], bool]:
    """Instantiate candidate model interface and metadata.

    Returns (model_instance, model_config, is_stub).
    """
    if model_arg.startswith("stub:"):
        behavior = model_arg.split(":", 1)[1]
        stub = StubModel(behavior=behavior, scenarios=golden_scenarios)
        config = {"model": model_arg, "stub": True, "behavior": behavior}
        return stub, config, True

    if model_arg in MODEL_LADDER:
        rung_spec = MODEL_LADDER[model_arg]
        aicredits_key = os.getenv("AICREDITS_API_KEY", "")
        aicredits_base = os.getenv("AICREDITS_BASE_URL", AICREDITS_BASE_URL)
        raw_model = LiteLLMModel(
            model_name=rung_spec["model"],
            provider=rung_spec.get("provider", "aicredits"),
            version="1.0.0",
            dry_run=False,
            api_base=aicredits_base,
            api_key=aicredits_key,
            custom_llm_provider="openai",
        )
        tracked = TrackedLiteLLMModel(raw_model)
        retry_policy = RetryPolicy(
            max_retries=5,
            initial_backoff_s=2.0,
            backoff_multiplier=2.0,
            max_backoff_s=30.0,
            seed=42,
        )
        resilient = ResilientModel(
            inner_model=tracked,
            retry_policy=retry_policy,
            circuit_breaker=CircuitBreaker(failure_threshold=5, cooldown_seconds=5.0),
        )
        config = {
            "model": model_arg,
            "stub": False,
            "model_id": rung_spec["model"],
            "provider": rung_spec.get("provider", "aicredits"),
            "input_price_per_m": rung_spec.get("input_price_per_m", 0.14),
            "output_price_per_m": rung_spec.get("output_price_per_m", 0.28),
        }
        return resilient, config, False

    raise ValueError(f"Unknown model argument '{model_arg}'. Expected 'stub:<behavior>' or one of {list(MODEL_LADDER.keys())}")


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="P11 Release Gate Evaluation")
    parser.add_argument("--model", type=str, required=True, help="Model rung (e.g. R2) or stub:<behavior>")
    parser.add_argument("--golden", type=str, default="projects/p11_release_gate/golden.json", help="Path to golden.json")
    parser.add_argument("--band", type=str, default="projects/p11_release_gate/band.json", help="Path to band.json or band_stub.json")
    parser.add_argument("--step-cap", type=int, default=24, help="Step cap per scenario (default: 24)")
    parser.add_argument("--concurrency", type=int, default=4, help="Worker concurrency for live runs (default: 4, stubs stay sequential)")
    parser.add_argument("--dry-run", action="store_true", help="Print cost estimate and exit")
    parser.add_argument("--confirm", action="store_true", help="Confirm execution of paid live runs")
    parser.add_argument("--report", type=str, default="report.json", help="Report output file name/path")
    parser.add_argument("--output-dir", type=str, default="projects/p11_release_gate", help="Output directory")

    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    start_utc = datetime.now(timezone.utc).isoformat()

    # Load golden manifest
    golden_file = resolve_path(args.golden, output_dir)
    if not golden_file.exists():
        print(f"Error: Golden file not found at {golden_file}", file=sys.stderr)
        return 1

    with open(golden_file, "r", encoding="utf-8") as f:
        golden_data = json.load(f)

    golden_ids = golden_data.get("golden_ids") or golden_data.get("ids", [])
    manifest_sha = golden_data.get("manifest_sha256", "")
    if not manifest_sha and golden_ids:
        manifest_sha = hashlib.sha256(json.dumps(golden_ids).encode("utf-8")).hexdigest()

    # Load band
    band_file = resolve_path(args.band, output_dir)
    if not band_file.exists():
        print(f"Error: Band file not found at {band_file}", file=sys.stderr)
        return 1

    with open(band_file, "r", encoding="utf-8") as f:
        band = json.load(f)

    # Setup corpus
    corpus = build_corpus()
    scenario_map = {s.scenario_id: s for s in corpus.scenarios}
    golden_scenarios = [scenario_map[sid] for sid in golden_ids if sid in scenario_map]
    if len(golden_scenarios) != len(golden_ids):
        print(f"Warning: Only found {len(golden_scenarios)}/{len(golden_ids)} golden scenarios in corpus", file=sys.stderr)

    # Setup model
    model, model_cfg, is_stub = make_model(args.model, golden_scenarios)

    # Setup ledger and price table
    price_table = PriceTable(
        rungs={
            k: RungPricing(
                model_name=v.get("name", k),
                input_price_per_m=v.get("input_price_per_m", 0.14),
                output_price_per_m=v.get("output_price_per_m", 0.28),
            )
            for k, v in MODEL_LADDER.items()
        }
    )
    ledger_path = output_dir / "ledger.jsonl"
    ledger = CostLedger(ledger_path=ledger_path)

    # Dry-run / confirmation check
    if not is_stub:
        runner = SweepRunner(
            project="p11_release",
            price_table=price_table,
            ledger=ledger,
            confirmed=args.confirm,
        )
        est_in = int(55000 * (args.step_cap / 24))
        est_out = int(3000 * (args.step_cap / 24))
        runner.dry_run(
            n_runs=len(golden_scenarios),
            in_tokens=est_in,
            out_tokens=est_out,
            rung=args.model,
        )

        if args.dry_run:
            print("Dry-run requested. Exiting without execution.")
            return 0

        if not args.confirm:
            print("Error: Paid sweep requires --confirm. Aborting.", file=sys.stderr)
            return 1
    else:
        if args.dry_run:
            print(f"Dry-run for stub model '{args.model}' ($0.00). Exiting without execution.")
            return 0

    # Execution
    trace_store = TraceStore(output_dir / "trace.db")
    env = {"documents": corpus.documents}

    outcomes: List[Dict[str, Any]] = []
    total_in_tok = 0
    total_out_tok = 0
    total_cost_usd = 0.0

    in_price = model_cfg.get("input_price_per_m", 0.14)
    out_price = model_cfg.get("output_price_per_m", 0.28)

    safe_model = args.model.replace(":", "_").replace("/", "_")
    sweep_output_path = output_dir / f"sweep_output_{safe_model}.json"

    effective_workers = args.concurrency if (args.concurrency > 1 and not is_stub) else 1
    print(f"Running P11 Release Gate on {len(golden_scenarios)} golden scenarios (model: {args.model}, concurrency: {effective_workers})...")

    save_lock = threading.Lock()
    stats_lock = threading.Lock()
    outcomes_map: Dict[str, Dict[str, Any]] = {}
    total_stats = {"in_tok": 0, "out_tok": 0, "cost_usd": 0.0}

    def _worker(s: Scenario) -> Dict[str, Any]:
        task = ScenarioTask(task_id=s.scenario_id, prompt=s.prompt, tier=s.tier)
        run_id = f"p11-{safe_model}-{s.scenario_id}"
        t_start = time.time()

        outcome = run_agent(
            task=task,
            env=env,
            model=model,
            step_cap=args.step_cap,
            trace_store=trace_store,
            run_id=run_id,
        )
        wall_ms = (time.time() - t_start) * 1000

        q_dict = {
            "id": s.scenario_id,
            "answer": s.final_answer,
            "required_source": s.required_source,
        }
        r_dict = {
            "answer": outcome.answer or "",
            "cited_sources": outcome.cited_sources,
        }
        verdict_dict = oracle_check(q_dict, r_dict)
        passed = bool(verdict_dict.get("passed", False))
        trace_store.record_verdict(run_id, s.scenario_id, passed)

        in_tok = 0
        out_tok = 0
        with trace_store._lock:
            cur = trace_store.conn.cursor()
            cur.execute(
                "SELECT SUM(prompt_tokens), SUM(completion_tokens) FROM spans WHERE run_id = ?",
                (run_id,),
            )
            row = cur.fetchone()
            in_tok = int(row[0] or 0) if row else 0
            out_tok = int(row[1] or 0) if row else 0

        cost_usd = (in_tok * in_price / 1e6) + (out_tok * out_price / 1e6) if not is_stub else 0.0

        with stats_lock:
            total_stats["in_tok"] += in_tok
            total_stats["out_tok"] += out_tok
            total_stats["cost_usd"] += cost_usd

        if not is_stub:
            ledger.record(
                LedgerEntry(
                    run_id=run_id,
                    project="p11_release",
                    rung=args.model,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    usd=cost_usd,
                    timestamp_utc=datetime.now(timezone.utc).isoformat(),
                )
            )

        outcome_dict = outcome.model_dump()
        outcome_dict["steps"] = outcome_dict["trace"]
        outcome_dict["scenario_id"] = s.scenario_id
        outcome_dict["run_id"] = run_id
        outcome_dict["tier"] = s.tier
        outcome_dict["grounded"] = passed
        outcome_dict["correct_answer"] = verdict_dict.get("correct", False)
        outcome_dict["cited_required"] = verdict_dict.get("cited_required", False)
        outcome_dict["wall_time_ms"] = wall_ms
        outcome_dict["input_tokens"] = in_tok
        outcome_dict["output_tokens"] = out_tok
        outcome_dict["cost_usd"] = cost_usd

        with stats_lock:
            outcomes_map[s.scenario_id] = outcome_dict

        save_sweep_output_incremental(sweep_output_path, outcome_dict, save_lock, golden_ids)

        status_flag = "PASS" if passed else "FAIL"
        print(f"  [{args.model}] {s.scenario_id} -> {status_flag} (steps={outcome.steps_used})")
        return outcome_dict

    if effective_workers > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=effective_workers) as pool_exec:
            futures = [pool_exec.submit(_worker, s) for s in golden_scenarios]
            for fut in concurrent.futures.as_completed(futures):
                fut.result()
    else:
        for s in golden_scenarios:
            _worker(s)

    outcomes = [outcomes_map[sid] for sid in golden_ids if sid in outcomes_map]
    print(f"Sweep output written to {sweep_output_path}")

    # Evaluate against tolerance band
    eval_result = evaluate(outcomes, band)
    verdict = eval_result["verdict"]

    end_utc = datetime.now(timezone.utc).isoformat()

    report = {
        "verdict": verdict,
        "metrics": eval_result["metrics"],
        "band": band,
        "band_file": Path(args.band).name,
        "regressions": eval_result["regressions"],
        "model_config_used": model_cfg,
        "golden_manifest_sha": manifest_sha,
        "timestamps": {
            "start_utc": start_utc,
            "end_utc": end_utc,
        },
        "spend": {
            "total_usd": total_stats["cost_usd"],
            "input_tokens": total_stats["in_tok"],
            "output_tokens": total_stats["out_tok"],
        },
    }

    report_arg_path = Path(args.report)
    if report_arg_path.is_absolute():
        report_path = report_arg_path
    elif len(report_arg_path.parts) == 1:
        report_path = output_dir / args.report
    else:
        report_path = report_arg_path
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Release gate report written to {report_path}")

    print("\n" + "=" * 60)
    print(f"RELEASE GATE VERDICT: {verdict}")
    print(f"  Golden Scenarios: {eval_result['metrics']['n_golden']}")
    print(f"  Pass Rate:        {eval_result['metrics']['pass_rate']:.4f} ({eval_result['metrics']['pass_count']}/{eval_result['metrics']['n_golden']})")
    print(f"  Malformed Rate:   {eval_result['metrics']['malformed_rate']:.4f} ({eval_result['metrics']['malformed_count']}/{eval_result['metrics']['n_golden']})")
    print(f"  Regressions:      {len(eval_result['regressions'])}")
    print("=" * 60)

    if verdict == "PASS":
        return 0
    elif verdict == "WARN":
        return 1
    else:
        return 2


if __name__ == "__main__":
    sys.exit(main())
