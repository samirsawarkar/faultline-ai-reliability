"""Sweep runner enforcing dry-run estimates, --confirm requirement, and mid-sweep budget stops."""
from __future__ import annotations

import json
import sys
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
    ) -> SweepOutput:
        """Execute sweep with per-call ledger updates and budget enforcement."""
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
        results: List[SweepItemResult] = []
        halted = False

        est_per_call = estimate(
            n_runs=1,
            in_tokens=in_tokens_est,
            out_tokens=out_tokens_est,
            rung=rung,
            price_table=self.price_table,
            cached_prefix_fraction=cached_prefix_fraction,
        )

        for task in tasks:
            task_id = get_task_id(task)

            # Check budget cap before each call with expected incremental cost
            try:
                self.ledger.check_cap(self.project, additional_usd=est_per_call)
            except BudgetExceeded as exc:
                halted = True
                print(f"BUDGET CAP HALT: {exc}", file=sys.stderr)
                self._save_partial(results, partial_output_path, rung, halted=True)
                raise exc

            output_val, success, usage = call_fn(task)

            # Compute actual USD cost
            if usage.usd is not None:
                cost_usd = usage.usd
            else:
                in_cost = (usage.input_tokens * pricing.input_price_per_m) / 1_000_000.0
                out_cost = (usage.output_tokens * pricing.output_price_per_m) / 1_000_000.0
                cost_usd = round(in_cost + out_cost, 6)

            # Write to ledger immediately
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
            results.append(item)
            self._save_partial(results, partial_output_path, rung, halted=False)

            # Check if this call consumed the remaining cap
            try:
                self.ledger.check_cap(self.project, additional_usd=0.0)
            except BudgetExceeded as exc:
                self._save_partial(results, partial_output_path, rung, halted=True)
                raise exc

        total_cost = sum(r.usage.usd or 0.0 for r in results)
        return SweepOutput(
            project=self.project,
            rung=rung,
            total_tasks=n_runs,
            completed_tasks=len(results),
            total_cost_usd=round(total_cost, 6),
            results=results,
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
