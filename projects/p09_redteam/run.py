"""Project P9: Adversarial Prompt Injection Regression Suite.

Evaluates prompt injection attacks through corpus document text across two arms:
Arm A: Bare agent (no RuntimePolicy)
Arm B: Agent protected by RuntimePolicy (P16 defaults)

Measures Attack Success Rate (ASR) per category, McNemar paired transitions,
and regenerates xfail-gated regression tests for attacks succeeding in Arm B.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple
import warnings

from dotenv import load_dotenv

warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("LiteLLM").setLevel(logging.ERROR)

from faultline_p2.agent.agent import run_agent
from faultline_p2.agent.contracts import AgentOutcome, AgentStep, OutcomeStatus, ScenarioTask
from faultline_p2.agent.model import LiteLLMModel, ModelInterface, ModelResponse, StubModel
from faultline_p2.config import AICREDITS_BASE_URL, MODEL_LADDER
from faultline_p2.cost.ledger import BudgetExceeded, CostLedger, LedgerEntry, PriceTable, RungPricing
from faultline_p2.env.corpus import Scenario, build_corpus
from faultline_p2.oracle._day01_oracle import oracle_check
from faultline_p2.policy import RuntimePolicy
from faultline_p2.redteam import (
    CATEGORIES,
    SEMANTIC_ANSWER_CATEGORIES,
    STRUCTURAL_CATEGORIES,
    Attack,
    HostileStub,
    build,
    check_benign_correct,
    inject,
    mentioned,
    succeeded,
)
from faultline_p2.resilience import CircuitBreaker, ResilientModel, RetryPolicy
from faultline_p2.stats import wilson_interval
from faultline_p2.stats.paired import mcnemar_from_pairs
from faultline_p2.trace.store import TraceStore

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TrackedLiteLLMModel:
    """Wraps LiteLLMModel to capture model name and token counts."""
    def __init__(self, inner: LiteLLMModel) -> None:
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


def select_scenarios(corpus: Any, n: int = 20) -> List[str]:
    """Select n scenarios deterministically from the standard pool restricted to T1 and T2.

    Why T1 and T2: T1 (1-hop) and T2 (3-hop) scenarios evaluate document prompt injection
    on the initial retrieval hop while bounding token counts (T1: 2,441 in / 540 out;
    T2: 18,089 in / 1,438 out) and latency compared to 5-hop T3 tasks.
    """
    eligible = [
        s for s in corpus.scenarios
        if s.pool == "standard" and s.tier in ("T1", "T2")
    ]
    # Sort deterministically by sha256(scenario_id)
    eligible.sort(key=lambda s: hashlib.sha256(s.scenario_id.encode("utf-8")).hexdigest())
    return [s.scenario_id for s in eligible[:n]]


def calculate_dry_run(
    scenarios: List[Scenario],
    categories: List[str],
    payloads_per_cat: int,
    arms: List[str],
    rung: str,
    ledger: CostLedger,
) -> Dict[str, Any]:
    """Compute dry-run cost estimate based on P1-measured tokens."""
    t1_scenarios = sum(1 for s in scenarios if s.tier == "T1")
    t2_scenarios = sum(1 for s in scenarios if s.tier == "T2")

    attacks_per_scenario = len(categories) * payloads_per_cat
    runs_per_arm = len(scenarios) * attacks_per_scenario
    total_runs = runs_per_arm * len(arms)

    t1_runs = t1_scenarios * attacks_per_scenario * len(arms)
    t2_runs = t2_scenarios * attacks_per_scenario * len(arms)

    # P1-measured tokens: T1 in=2441, out=540; T2 in=18089, out=1438
    total_in = t1_runs * 2441 + t2_runs * 18089
    total_out = t1_runs * 540 + t2_runs * 1438

    pricing = MODEL_LADDER.get(rung, {})
    in_price = pricing.get("input_price_per_m", 0.14)
    out_price = pricing.get("output_price_per_m", 0.28)

    est_cost = (total_in * in_price + total_out * out_price) / 1_000_000

    cap = ledger.project_caps.get("p09_redteam", 6.00)
    spent = ledger.spent("p09_redteam")
    remaining = max(0.0, cap - spent)

    return {
        "arms": arms,
        "scenarios_count": len(scenarios),
        "t1_count": t1_scenarios,
        "t2_count": t2_scenarios,
        "attacks_per_arm": runs_per_arm,
        "total_runs": total_runs,
        "total_in_tokens": total_in,
        "total_out_tokens": total_out,
        "est_cost_usd": est_cost,
        "cap_usd": cap,
        "spent_usd": spent,
        "remaining_usd": remaining,
    }


def save_sweep_incremental(
    sweep_file: Path,
    record: Dict[str, Any],
    lock: threading.Lock,
) -> None:
    """Incrementally append/save an attack outcome record to the sweep file."""
    with lock:
        items = []
        if sweep_file.exists():
            try:
                with open(sweep_file, "r", encoding="utf-8") as f:
                    items = json.load(f)
            except Exception:
                items = []
        items.append(record)
        tmp_p = sweep_file.with_suffix(".tmp")
        with open(tmp_p, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)
        tmp_p.replace(sweep_file)


def run_single_attack(
    attack: Attack,
    scenario: Scenario,
    corpus: Any,
    arm: str,
    rung: str,
    step_cap: int,
    model_factory: Any,
    trace_store: TraceStore,
    sweep_file: Path,
    lock: threading.Lock,
    ledger: Optional[CostLedger] = None,
    is_stub: bool = False,
) -> Dict[str, Any]:
    """Execute a single attack in the designated arm (A or B)."""
    run_id = f"{rung}-{arm}-{attack.attack_id}"
    env_docs = inject(corpus.documents, attack)

    policy: Optional[RuntimePolicy] = None
    if arm == "B":
        policy = RuntimePolicy()
        policy.reset_run(run_id)
        env = {"documents": env_docs, "policy": policy}
    else:
        env = {"documents": env_docs}

    model = model_factory()
    task = ScenarioTask(task_id=scenario.scenario_id, prompt=scenario.prompt, tier=scenario.tier)

    outcome = run_agent(
        task=task,
        env=env,
        model=model,
        step_cap=step_cap,
        trace_store=trace_store,
        run_id=run_id,
        policy=policy,
    )

    # Read policy decisions logged for this run
    decisions = []
    try:
        with trace_store._lock:
            cur = trace_store.conn.cursor()
            cur.execute(
                "SELECT tool_name, allowed, rule, reason FROM policy_decisions WHERE run_id = ?",
                (run_id,),
            )
            decisions = [
                {"tool": r[0], "allowed": bool(r[1]), "rule": r[2], "reason": r[3]}
                for r in cur.fetchall()
            ]
    except Exception:
        pass

    # Sum prompt and completion tokens from trace_store spans for this run_id
    in_tok = 0
    out_tok = 0
    try:
        with trace_store._lock:
            cur = trace_store.conn.cursor()
            cur.execute(
                "SELECT SUM(prompt_tokens), SUM(completion_tokens) FROM spans WHERE run_id = ?",
                (run_id,),
            )
            row = cur.fetchone()
            in_tok = int(row[0] or 0) if row else 0
            out_tok = int(row[1] or 0) if row else 0
    except Exception:
        pass

    pricing = MODEL_LADDER.get(rung, {})
    in_price = float(pricing.get("input_price_per_m", 0.14))
    out_price = float(pricing.get("output_price_per_m", 0.28))
    cost_usd = round((in_tok * in_price / 1e6) + (out_tok * out_price / 1e6), 6)

    if not is_stub and ledger is not None:
        entry = LedgerEntry(
            run_id=run_id,
            project="p09_redteam",
            rung=rung,
            input_tokens=in_tok,
            output_tokens=out_tok,
            usd=cost_usd,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
        )
        ledger.record(entry)
        ledger.check_cap("p09_redteam")

    benign_corr = check_benign_correct(scenario, outcome)
    mention = mentioned(attack, outcome, outcome.trace, decisions)
    attack_succ = succeeded(attack, outcome, outcome.trace, decisions, benign_correct=benign_corr)

    record = {
        "attack_id": attack.attack_id,
        "category": attack.category,
        "scenario_id": attack.scenario_id,
        "payload": attack.payload,
        "target_doc_id": attack.target_doc_id,
        "expected_fake_answer": attack.expected_fake_answer,
        "decoy_doc": attack.decoy_doc,
        "arm": arm,
        "run_id": run_id,
        "status": outcome.status.value,
        "answer": outcome.answer,
        "cited_sources": outcome.cited_sources,
        "steps_used": outcome.steps_used,
        "reason": outcome.reason,
        "attack_success": attack_succ,
        "mention": mention,
        "benign_correct": benign_corr,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "cost_usd": cost_usd,
        "trace": [s.model_dump() for s in outcome.trace],
        "policy_decisions": decisions,
    }

    save_sweep_incremental(sweep_file, record, lock)
    return record


def generate_regression_tests(
    results: Dict[str, Any],
    output_path: Path,
) -> None:
    """Generate tests/phase2/test_p09_regressions.py from results.json."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    open_regs = results.get("open_regressions", [])

    lines = [
        "# GENERATED by projects/p09_redteam/run.py --regenerate-tests — do not edit",
        "from __future__ import annotations",
        "",
        "import pytest",
        "from faultline_p2.agent.agent import run_agent",
        "from faultline_p2.agent.contracts import ScenarioTask",
        "from faultline_p2.env.corpus import build_corpus",
        "from faultline_p2.policy import RuntimePolicy",
        "from faultline_p2.redteam import Attack, HostileStub, check_benign_correct, inject, succeeded",
        "from projects.p09_redteam.run import select_scenarios",
        "",
        "CORPUS = build_corpus()",
        "SCENARIOS_BY_ID = {s.scenario_id: s for s in CORPUS.scenarios}",
        "",
    ]

    for cat in ["tool_exfil_path", "unlisted_tool", "query_dump", "budget_loop"]:
        lines.extend([
            f"def test_invariant_{cat}() -> None:",
            f'    """Assert RuntimePolicy deterministically blocks HostileStub for structural category: {cat}."""',
            f"    from faultline_p2.redteam import build",
            f"    sc_ids = select_scenarios(CORPUS, n=5)",
            f'    attacks = [a for a in build(CORPUS, sc_ids, seed=42) if a.category == "{cat}"]',
            f"    assert len(attacks) >= 5",
            f"    for a in attacks:",
            f"        sc = SCENARIOS_BY_ID[a.scenario_id]",
            f"        policy = RuntimePolicy()",
            f'        run_id = f"invariant-{cat}-{{a.attack_id}}"',
            f"        policy.reset_run(run_id)",
            f'        env = {{"documents": inject(CORPUS.documents, a), "policy": policy}}',
            f"        task = ScenarioTask(task_id=sc.scenario_id, prompt=sc.prompt, tier=sc.tier)",
            f"        model = HostileStub()",
            f"        outcome = run_agent(task, env, model, step_cap=12, run_id=run_id, policy=policy)",
            f'        assert not succeeded(a, outcome, outcome.trace, []), f"Invariant failed: {cat} succeeded against policy"',
            "",
        ])

    for reg in sorted(open_regs, key=lambda x: x["attack_id"]):
        atk_id = reg["attack_id"]
        cat = reg["category"]
        sc_id = reg["scenario_id"]
        safe_name = atk_id.replace("-", "_")

        lines.extend([
            f'@pytest.mark.xfail(strict=True, reason="P9 open regression: {cat} {atk_id}")',
            f"def test_regression_{safe_name}() -> None:",
            f'    sc = SCENARIOS_BY_ID["{sc_id}"]',
            f"    from faultline_p2.redteam import build",
            f'    attacks = [a for a in build(CORPUS, ["{sc_id}"], seed=42) if a.attack_id == "{atk_id}"]',
            f'    assert len(attacks) == 1, "Attack definition missing"',
            f"    attack = attacks[0]",
            f"    policy = RuntimePolicy()",
            f'    run_id = f"repro-{atk_id}"',
            f"    policy.reset_run(run_id)",
            f'    env = {{"documents": inject(CORPUS.documents, attack), "policy": policy}}',
            f"    task = ScenarioTask(task_id=sc.scenario_id, prompt=sc.prompt, tier=sc.tier)",
            f"    model = HostileStub()",
            f"    outcome = run_agent(task, env, model, step_cap=12, run_id=run_id, policy=policy)",
            f'    assert not succeeded(attack, outcome, outcome.trace, [], benign_correct=check_benign_correct(sc, outcome)), "Attack still succeeded against policy"',
            "",
        ])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def make_live_model(rung_or_cfg: Any = "R2") -> ResilientModel:
    if isinstance(rung_or_cfg, dict):
        pricing = rung_or_cfg
        model_name = pricing.get("model_name", "z-ai/glm-5.3-flash")
        provider = pricing.get("provider", "aicredits")
        version = pricing.get("version", "1.0")
    else:
        rung = str(rung_or_cfg)
        pricing = MODEL_LADDER.get(rung, {})
        model_name = pricing.get("model_name", os.getenv(f"MODEL_{rung}", "z-ai/glm-5.3-flash"))
        provider = pricing.get("provider", "aicredits")
        version = pricing.get("version", "1.0")

    aicredits_key = os.getenv("AICREDITS_API_KEY")
    aicredits_base = os.getenv("AICREDITS_BASE_URL", AICREDITS_BASE_URL)
    raw_model = LiteLLMModel(
        model_name=model_name,
        provider=provider,
        version=version,
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


_live_factory = make_live_model
make_model = make_live_model
live_factory = make_live_model


def main() -> int:
    parser = argparse.ArgumentParser(description="P9 Redteam Prompt Injection Benchmark")
    parser.add_argument("--rung", type=str, default="R2", help="Model ladder rung (e.g. R2)")
    parser.add_argument("--arms", type=str, default="A,B", help="Comma-separated arms to evaluate (e.g. A,B)")
    parser.add_argument("--scenarios", type=int, default=20, help="Number of scenarios to evaluate (default 20)")
    parser.add_argument("--payloads-per-category", type=int, default=1, help="Payloads per category (default 1)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default 42)")
    parser.add_argument("--step-cap", type=int, default=12, help="Step cap per run (default 12)")
    parser.add_argument("--concurrency", type=int, default=4, help="Worker concurrency (default 4)")
    parser.add_argument("--dry-run", action="store_true", help="Print cost estimate and exit")
    parser.add_argument("--confirm", action="store_true", help="Confirm paid execution")
    parser.add_argument("--stub", type=str, choices=["hostile", "solver"], default=None, help="Stub model behavior")
    parser.add_argument("--output-dir", type=str, default="projects/p09_redteam", help="Output directory")
    parser.add_argument("--rescore", action="store_true", help="Rebuild results.json from existing sweep_output files without model calls")
    parser.add_argument("--regenerate-tests", action="store_true", help="Regenerate tests/phase2/test_p09_regressions.py")
    parser.add_argument("--tests-out", type=str, default="tests/phase2/test_p09_regressions.py", help="Output file path for regenerated tests")

    args = parser.parse_args()
    load_dotenv()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    arms = [a.strip().upper() for a in args.arms.split(",") if a.strip()]

    corpus = build_corpus()
    scenario_ids = select_scenarios(corpus, n=args.scenarios)
    selected_scenarios = [s for s in corpus.scenarios if s.scenario_id in set(scenario_ids)]
    scenarios_by_id = {s.scenario_id: s for s in selected_scenarios}

    ledger_path = output_dir / "ledger.jsonl"
    ledger = CostLedger(ledger_path)

    # Dry-run handling
    if args.dry_run:
        estimate = calculate_dry_run(
            scenarios=selected_scenarios,
            categories=CATEGORIES,
            payloads_per_cat=args.payloads_per_category,
            arms=arms,
            rung=args.rung,
            ledger=ledger,
        )
        print("============================================================")
        print(f"DRY-RUN COST ESTIMATE: Project [p09_redteam] / Rung [{args.rung}]")
        print(f"  Arms:               {', '.join(estimate['arms'])}")
        print(f"  Scenarios:          {estimate['scenarios_count']} (T1: {estimate['t1_count']}, T2: {estimate['t2_count']})")
        print(f"  Attacks per Arm:    {estimate['attacks_per_arm']}")
        print(f"  Total Runs:         {estimate['total_runs']}")
        print(f"  Est. Tokens / Run:  T1: in=2441, out=540 | T2: in=18089, out=1438")
        print(f"  Est. Total In:      {estimate['total_in_tokens']:,} | Out: {estimate['total_out_tokens']:,}")
        print(f"  Est. Total Cost:    ${estimate['est_cost_usd']:.6f} USD")
        print(f"  Project Cap:        ${estimate['cap_usd']:.2f} USD (Spent: ${estimate['spent_usd']:.4f}, Remaining: ${estimate['remaining_usd']:.4f})")
        print("============================================================")
        print("Dry-run requested. Exiting without execution.")
        return 0

    sweep_records_by_arm: Dict[str, List[Dict[str, Any]]] = {}

    if args.rescore:
        print(f"Rescoring existing sweep output files for rung {args.rung}, arms {arms} without running model calls...")
        for arm in arms:
            sweep_file = output_dir / f"sweep_output_{args.rung}_{arm}.json"
            if not sweep_file.exists():
                print(f"Error: Sweep file {sweep_file} not found for rescoring.")
                return 1
            with open(sweep_file, "r", encoding="utf-8") as f:
                recs = json.load(f)

            rescored_recs = []
            for r in recs:
                atk = Attack(
                    attack_id=r["attack_id"],
                    category=r["category"],
                    scenario_id=r["scenario_id"],
                    payload=r["payload"],
                    target_doc_id=r["target_doc_id"],
                    expected_fake_answer=r.get("expected_fake_answer"),
                    decoy_doc=r.get("decoy_doc"),
                )
                outcome = AgentOutcome(
                    task_id=r["scenario_id"],
                    status=OutcomeStatus(r["status"]),
                    answer=r.get("answer"),
                    cited_sources=r.get("cited_sources") or [],
                    steps_used=r.get("steps_used", 0),
                    step_cap=12,
                    reason=r.get("reason"),
                    trace=[AgentStep(**s) for s in r.get("trace", [])],
                )
                decisions = r.get("policy_decisions", [])
                benign_corr = bool(r.get("benign_correct", False))
                mention = mentioned(atk, outcome, outcome.trace, decisions)
                attack_succ = succeeded(atk, outcome, outcome.trace, decisions, benign_correct=benign_corr)

                r["mention"] = mention
                r["attack_success"] = attack_succ
                rescored_recs.append(r)

            with open(sweep_file, "w", encoding="utf-8") as f:
                json.dump(rescored_recs, f, indent=2)
            sweep_records_by_arm[arm] = rescored_recs

        attacks = [
            Attack(
                attack_id=r["attack_id"],
                category=r["category"],
                scenario_id=r["scenario_id"],
                payload=r["payload"],
                target_doc_id=r["target_doc_id"],
                expected_fake_answer=r.get("expected_fake_answer"),
                decoy_doc=r.get("decoy_doc"),
            )
            for r in sweep_records_by_arm[arms[0]]
        ]
        scenario_ids = sorted(list({r["scenario_id"] for r in sweep_records_by_arm[arms[0]]}))
    else:
        # Gate live execution
        if not args.stub and not args.confirm:
            print("Error: Live paid runs require --confirm. Refusing execution without confirmation.")
            return 1

        # Model factory
        if args.stub == "hostile":
            model_factory = lambda: HostileStub()
            is_stub = True
        elif args.stub == "solver":
            model_factory = lambda: StubModel(behavior="solver")
            is_stub = True
        else:
            is_stub = False
            model_factory = lambda: make_live_model(args.rung)

        attacks = build(corpus, scenario_ids, seed=args.seed, payloads_per_category=args.payloads_per_category)
        print(f"Built {len(attacks)} attacks across {len(scenario_ids)} scenarios ({len(CATEGORIES)} categories).")

        trace_store = TraceStore(str(output_dir / "trace.db"))
        sweep_lock = threading.Lock()

        concurrency = 1 if is_stub else max(1, args.concurrency)

        for arm in arms:
            sweep_file = output_dir / f"sweep_output_{args.rung}_{arm}.json"
            if sweep_file.exists():
                sweep_file.unlink()

            print(f"\n--- Running Arm {arm} ({len(attacks)} attacks, concurrency {concurrency}) ---")
            arm_records: List[Dict[str, Any]] = []

            if concurrency > 1:
                with ThreadPoolExecutor(max_workers=concurrency) as executor:
                    futures = [
                        executor.submit(
                            run_single_attack,
                            attack=atk,
                            scenario=scenarios_by_id[atk.scenario_id],
                            corpus=corpus,
                            arm=arm,
                            rung=args.rung,
                            step_cap=args.step_cap,
                            model_factory=model_factory,
                            trace_store=trace_store,
                            sweep_file=sweep_file,
                            lock=sweep_lock,
                            ledger=ledger,
                            is_stub=is_stub,
                        )
                        for atk in attacks
                    ]
                    for f in futures:
                        arm_records.append(f.result())
            else:
                for atk in attacks:
                    rec = run_single_attack(
                        attack=atk,
                        scenario=scenarios_by_id[atk.scenario_id],
                        corpus=corpus,
                        arm=arm,
                        rung=args.rung,
                        step_cap=args.step_cap,
                        model_factory=model_factory,
                        trace_store=trace_store,
                        sweep_file=sweep_file,
                        lock=sweep_lock,
                        ledger=ledger,
                        is_stub=is_stub,
                    )
                    arm_records.append(rec)

            sweep_records_by_arm[arm] = arm_records

    # Compile results.json
    per_category: Dict[str, Dict[str, Any]] = {}
    pooled: Dict[str, Dict[str, Any]] = {}

    for arm in arms:
        recs = sweep_records_by_arm.get(arm, [])
        total_succ = sum(1 for r in recs if r["attack_success"])
        total_mention = sum(1 for r in recs if r.get("mention", False))
        total_n = len(recs)
        pooled_lo, pooled_hi = wilson_interval(total_succ, total_n, confidence=0.95)
        pooled[arm] = {
            "n": total_n,
            "attack_success_count": total_succ,
            "asr": total_succ / total_n if total_n > 0 else 0.0,
            "wilson_ci": [round(pooled_lo, 4), round(pooled_hi, 4)],
            "mention_count": total_mention,
            "mention_rate": total_mention / total_n if total_n > 0 else 0.0,
            "benign_correct_count": sum(1 for r in recs if r.get("benign_correct", False)),
            "benign_correct_rate": sum(1 for r in recs if r.get("benign_correct", False)) / total_n if total_n > 0 else 0.0,
        }

    for cat in CATEGORIES:
        per_category[cat] = {}
        for arm in arms:
            recs = [r for r in sweep_records_by_arm.get(arm, []) if r["category"] == cat]
            n = len(recs)
            succ = sum(1 for r in recs if r["attack_success"])
            mention_cnt = sum(1 for r in recs if r.get("mention", False))
            lo, hi = wilson_interval(succ, n, confidence=0.95)
            benign_cnt = sum(1 for r in recs if r.get("benign_correct", False))
            per_category[cat][arm] = {
                "n": n,
                "attack_success_count": succ,
                "asr": succ / n if n > 0 else 0.0,
                "wilson_ci": [round(lo, 4), round(hi, 4)],
                "mention_count": mention_cnt,
                "mention_rate": mention_cnt / n if n > 0 else 0.0,
                "benign_correct_count": benign_cnt,
                "benign_correct_rate": benign_cnt / n if n > 0 else 0.0,
            }

    # McNemar tests
    mcnemar_stats: Dict[str, Any] = {}
    if "A" in arms and "B" in arms:
        a_by_id = {r["attack_id"]: r for r in sweep_records_by_arm["A"]}
        b_by_id = {r["attack_id"]: r for r in sweep_records_by_arm["B"]}
        all_ids = [atk.attack_id for atk in attacks]

        for cat in CATEGORIES:
            cat_ids = [aid for aid in all_ids if a_by_id[aid]["category"] == cat]
            a_vec = [a_by_id[aid]["attack_success"] for aid in cat_ids]
            b_vec = [b_by_id[aid]["attack_success"] for aid in cat_ids]
            mcnemar_stats[cat] = mcnemar_from_pairs(a_vec, b_vec)

        all_a_vec = [a_by_id[aid]["attack_success"] for aid in all_ids]
        all_b_vec = [b_by_id[aid]["attack_success"] for aid in all_ids]
        mcnemar_stats["pooled"] = mcnemar_from_pairs(all_a_vec, all_b_vec)

    # Open regressions (attacks succeeding in Arm B)
    open_regs = []
    if "B" in arms:
        for r in sweep_records_by_arm["B"]:
            if r["attack_success"]:
                open_regs.append({
                    "attack_id": r["attack_id"],
                    "category": r["category"],
                    "scenario_id": r["scenario_id"],
                })

    results = {
        "manifest": {
            "project": "p09_redteam",
            "rung": args.rung,
            "stub": args.stub,
            "arms": arms,
            "scenarios_count": len(scenario_ids),
            "scenario_ids": scenario_ids,
            "corpus_sha256": corpus.content_hash,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
        "per_category": per_category,
        "pooled": pooled,
        "mcnemar": mcnemar_stats,
        "open_regressions": open_regs,
        "open_regressions_count": len(open_regs),
        "spend_usd": ledger.spent("p09_redteam"),
    }

    results_path = output_dir / "results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {results_path}")

    # Print pretty summary table
    print("\n" + "=" * 115)
    model_disp = f"stub:{args.stub}" if args.stub else args.rung
    if args.rescore:
        model_disp += " (rescored)"
    print(f"P9 REDTEAM BENCHMARK RESULTS (Model: {model_disp}, Scenarios: {len(scenario_ids)})")
    print("=" * 115)
    print(f"{'Category':20s} {'Arm A ASR (95% CI)':28s} {'Arm A Mention':14s} {'Arm B ASR (95% CI)':28s} {'Arm B Mention':14s} {'McNemar p':10s}")
    print("-" * 115)
    for cat in CATEGORIES:
        a_stat = per_category[cat].get("A", {})
        b_stat = per_category[cat].get("B", {})
        a_txt = f"{a_stat.get('asr', 0.0)*100:5.1f}% [{a_stat.get('wilson_ci', [0,0])[0]*100:4.1f}%, {a_stat.get('wilson_ci', [0,0])[1]*100:4.1f}%]" if a_stat else "N/A"
        b_txt = f"{b_stat.get('asr', 0.0)*100:5.1f}% [{b_stat.get('wilson_ci', [0,0])[0]*100:4.1f}%, {b_stat.get('wilson_ci', [0,0])[1]*100:4.1f}%]" if b_stat else "N/A"
        a_m_txt = f"{a_stat.get('mention_rate', 0.0)*100:5.1f}%" if a_stat else "N/A"
        b_m_txt = f"{b_stat.get('mention_rate', 0.0)*100:5.1f}%" if b_stat else "N/A"
        p_val = mcnemar_stats.get(cat, {}).get("p_value")
        p_txt = f"{p_val:.4f}" if p_val is not None else "N/A"
        print(f"{cat:20s} {a_txt:28s} {a_m_txt:14s} {b_txt:28s} {b_m_txt:14s} {p_txt:10s}")

    print("-" * 115)
    p_a = pooled.get("A", {})
    p_b = pooled.get("B", {})
    pa_txt = f"{p_a.get('asr', 0.0)*100:5.1f}% [{p_a.get('wilson_ci', [0,0])[0]*100:4.1f}%, {p_a.get('wilson_ci', [0,0])[1]*100:4.1f}%]" if p_a else "N/A"
    pb_txt = f"{p_b.get('asr', 0.0)*100:5.1f}% [{p_b.get('wilson_ci', [0,0])[0]*100:4.1f}%, {p_b.get('wilson_ci', [0,0])[1]*100:4.1f}%]" if p_b else "N/A"
    pa_m_txt = f"{p_a.get('mention_rate', 0.0)*100:5.1f}%" if p_a else "N/A"
    pb_m_txt = f"{p_b.get('mention_rate', 0.0)*100:5.1f}%" if p_b else "N/A"
    pooled_p = mcnemar_stats.get("pooled", {}).get("p_value")
    pooled_p_txt = f"{pooled_p:.4f}" if pooled_p is not None else "N/A"
    print(f"{'POOLED':20s} {pa_txt:28s} {pa_m_txt:14s} {pb_txt:28s} {pb_m_txt:14s} {pooled_p_txt:10s}")
    print("=" * 115)
    print(f"Open Regressions in Arm B: {len(open_regs)} / {len(attacks)} attacks")

    if args.regenerate_tests:
        test_file = Path(args.tests_out)
        if not test_file.is_absolute():
            test_file = REPO_ROOT / test_file
        generate_regression_tests(results, test_file)
        print(f"Wrote generated regression tests to {test_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
