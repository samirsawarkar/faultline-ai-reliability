"""Sweep runner enforcing dry-run estimates, --confirm requirement, concurrent execution, and mid-sweep budget stops."""
from __future__ import annotations

import concurrent.futures
import json
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from faultline_p2.cost.ledger import (
    BudgetExceeded,
    CostLedger,
    LedgerEntry,
    PriceTable,
    estimate,
)

_STRICT = ConfigDict(extra="forbid")
T = TypeVar("T")


class CallUsage(BaseModel):
    model_config = _STRICT
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    usd: Optional[float] = Field(default=None, ge=0.0)


class SweepItemResult(BaseModel):
    model_config = _STRICT
    task_id: str
    success: bool
    output: Any
    usage: CallUsage


class SweepOutput(BaseModel):
    model_config = _STRICT
    project: str
    rung: str
    total_tasks: int
    completed_tasks: int
    total_cost_usd: float
    results: List[SweepItemResult]
    halted_due_to_budget: bool = False


class SweepRunner:
    """The unified runner used across all Phase 2 projects."""

    def __init__(
        self,
        project: str,
        price_table: PriceTable,
        ledger: CostLedger,
        confirmed: bool = False,
    ) -> None:
        self.project = project
        self.price_table = price_table
        self.ledger = ledger
        self.confirmed = confirmed

    def dry_run(
        self,
        n_runs: int,
        in_tokens: int,
        out_tokens: int,
        rung: str,
        cached_prefix_fraction: float = 0.0,
    ) -> float:
        """Estimate cost, check remaining budget cap, and print summary to stdout."""
        est_cost = estimate(
            n_runs=n_runs,
            in_tokens=in_tokens,
            out_tokens=out_tokens,
            rung=rung,
            price_table=self.price_table,
            cached_prefix_fraction=cached_prefix_fraction,
        )
        spent = self.ledger.spent(self.project)
        cap = self.ledger.project_caps.get(self.project, 0.0)
        remaining = cap - spent

        print("=" * 60)
        print(f"DRY-RUN COST ESTIMATE: Project [{self.project}] / Rung [{rung}]")
        print(f"  Runs:               {n_runs}")
        print(f"  Est. Tokens / Run:  in={in_tokens}, out={out_tokens}")
        print(f"  Est. Total Cost:    ${est_cost:.6f} USD")
        print(f"  Project Cap:        ${cap:.2f} USD (Spent: ${spent:.4f}, Remaining: ${remaining:.4f})")
        print("=" * 60)
        return est_cost

    def execute_sweep(
        self,
        tasks: Sequence[T],
        get_task_id: Callable[[T], str],
        call_fn: Callable[[T], tuple[Any, bool, CallUsage]],
        in_tokens_est: int,
        out_tokens_est: int,
        rung: str,
        cached_prefix_fraction: float = 0.0,
        partial_output_path: Optional[Path] = None,
        max_workers: int = 10,
        concurrency: Optional[int] = None,
    ) -> SweepOutput:
        """Execute sweep with concurrent workers, per-call ledger updates, and budget enforcement."""
        n_runs = len(tasks)
        est_cost = self.dry_run(
            n_runs=n_runs,
            in_tokens=in_tokens_est,
            out_tokens=out_tokens_est,
            rung=rung,
            cached_prefix_fraction=cached_prefix_fraction,
        )

        if not self.confirmed:
            print("SWEEP REFUSED: --confirm flag not provided. Zero paid calls made.", file=sys.stderr)
            raise RuntimeError(
                f"Sweep for project '{self.project}' requires explicit --confirm. "
                f"Estimated cost: ${est_cost:.6f} USD."
            )

        # Verify we are under cap before starting
        self.ledger.check_cap(self.project, additional_usd=0.0)

        pricing = self.price_table.get_rung(rung)
        est_per_call = estimate(
            n_runs=1,
            in_tokens=in_tokens_est,
            out_tokens=out_tokens_est,
            rung=rung,
            price_table=self.price_table,
            cached_prefix_fraction=cached_prefix_fraction,
        )

        effective_workers = concurrency if concurrency is not None else max_workers
        effective_workers = max(1, effective_workers)

        results_by_index: Dict[int, SweepItemResult] = {}
        pending_reservations_usd = 0.0
        sweep_lock = threading.Lock()
        stop_event = threading.Event()
        first_budget_exc: Optional[BudgetExceeded] = None

        def worker_task(index: int, task: T) -> Optional[SweepItemResult]:
            nonlocal pending_reservations_usd, first_budget_exc

            if stop_event.is_set():
                return None

            task_id = get_task_id(task)

            # 1. Check & reserve budget before starting call
            with sweep_lock:
                if stop_event.is_set():
                    return None
                try:
                    self.ledger.check_cap(self.project, additional_usd=pending_reservations_usd + est_per_call)
                    pending_reservations_usd += est_per_call
                except BudgetExceeded as exc:
                    if first_budget_exc is None:
                        first_budget_exc = exc
                    stop_event.set()
                    current_results = [results_by_index[i] for i in sorted(results_by_index.keys())]
                    self._save_partial(current_results, partial_output_path, rung, halted=True)
                    raise exc

            # 2. Execute call outside lock
            try:
                output_val, success, usage = call_fn(task)
            except Exception as e:
                with sweep_lock:
                    pending_reservations_usd = max(0.0, pending_reservations_usd - est_per_call)
                raise e

            # 3. Calculate actual USD cost
            if usage.usd is not None:
                cost_usd = usage.usd
            else:
                in_cost = (usage.input_tokens * pricing.input_price_per_m) / 1_000_000.0
                out_cost = (usage.output_tokens * pricing.output_price_per_m) / 1_000_000.0
                cost_usd = round(in_cost + out_cost, 6)

            # 4. Record to ledger and results under lock
            with sweep_lock:
                pending_reservations_usd = max(0.0, pending_reservations_usd - est_per_call)

                entry = LedgerEntry(
                    run_id=task_id,
                    project=self.project,
                    rung=rung,
                    input_tokens=usage.input_tokens,
                    output_tokens=usage.output_tokens,
                    usd=cost_usd,
                    timestamp_utc=datetime.now(timezone.utc).isoformat(),
                )
                self.ledger.record(entry)

                item = SweepItemResult(
                    task_id=task_id,
                    success=success,
                    output=output_val,
                    usage=CallUsage(
                        input_tokens=usage.input_tokens,
                        output_tokens=usage.output_tokens,
                        usd=cost_usd,
                    ),
                )
                results_by_index[index] = item

                current_results = [results_by_index[i] for i in sorted(results_by_index.keys())]
                self._save_partial(current_results, partial_output_path, rung, halted=False)

                # Check if this call pushed the ledger over cap
                try:
                    self.ledger.check_cap(self.project, additional_usd=0.0)
                except BudgetExceeded as exc:
                    if first_budget_exc is None:
                        first_budget_exc = exc
                    stop_event.set()
                    self._save_partial(current_results, partial_output_path, rung, halted=True)
                    raise exc

                return item

        # Execute using ThreadPoolExecutor
        if effective_workers == 1:
            for idx, task in enumerate(tasks):
                try:
                    worker_task(idx, task)
                except BudgetExceeded:
                    break
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=effective_workers) as executor:
                futures = {executor.submit(worker_task, idx, task): idx for idx, task in enumerate(tasks)}
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()
                    except BudgetExceeded:
                        pass
                    except Exception as exc:
                        # Re-raise unexpected execution errors
                        print(f"Error in worker task: {exc}", file=sys.stderr)

        sorted_results = [results_by_index[i] for i in sorted(results_by_index.keys())]

        if first_budget_exc is not None:
            self._save_partial(sorted_results, partial_output_path, rung, halted=True)
            print(f"BUDGET CAP HALT: {first_budget_exc}", file=sys.stderr)
            raise first_budget_exc

        total_cost = sum(r.usage.usd or 0.0 for r in sorted_results)
        return SweepOutput(
            project=self.project,
            rung=rung,
            total_tasks=n_runs,
            completed_tasks=len(sorted_results),
            total_cost_usd=round(total_cost, 6),
            results=sorted_results,
            halted_due_to_budget=False,
        )

    def _save_partial(
        self,
        results: List[SweepItemResult],
        path: Optional[Path],
        rung: str,
        halted: bool,
    ) -> None:
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            output = SweepOutput(
                project=self.project,
                rung=rung,
                total_tasks=len(results),
                completed_tasks=len(results),
                total_cost_usd=round(sum(r.usage.usd or 0.0 for r in results), 6),
                results=results,
                halted_due_to_budget=halted,
            )
            with open(path, "w", encoding="utf-8") as f:
                f.write(json.dumps(output.model_dump(), indent=2, sort_keys=True) + "\n")
