"""Tests for cost ledger, budget stop, and sweep runner."""
import json
from pathlib import Path

import pytest

from faultline_p2.cost.ledger import (
    BudgetExceeded,
    CostLedger,
    PriceTable,
    RungPricing,
    estimate,
)
from faultline_p2.sweep.runner import CallUsage, SweepRunner


@pytest.fixture
def sample_price_table():
    return PriceTable(
        rungs={
            "R1": RungPricing(
                model_name="gemini-2.5-flash-lite",
                input_price_per_m=0.10,
                output_price_per_m=0.40,
                cached_input_price_per_m=0.05,
            ),
            "R2": RungPricing(
                model_name="deepseek-v4-flash",
                input_price_per_m=0.14,
                output_price_per_m=0.28,
                cached_input_price_per_m=0.07,
            ),
        }
    )


def test_estimate_hand_computed_arithmetic(sample_price_table):
    # Hand-computed arithmetic:
    # R1: input = $0.10 / 1M, output = $0.40 / 1M, cached_input = $0.05 / 1M
    # n_runs = 100
    # in_tokens = 10,000
    # out_tokens = 2,500
    # cached_prefix_fraction = 0.60 (60% cached)
    #
    # Uncached in_tokens = 10,000 * 0.40 = 4,000 tokens -> 4,000 * $0.10 / 1,000,000 = $0.00040
    # Cached in_tokens   = 10,000 * 0.60 = 6,000 tokens -> 6,000 * $0.05 / 1,000,000 = $0.00030
    # Total input cost per run = $0.00070
    # Output tokens     = 2,500 tokens -> 2,500 * $0.40 / 1,000,000 = $0.00100
    # Total per run = $0.00070 + $0.00100 = $0.00170
    # Total for 100 runs = 100 * $0.00170 = $0.170000 USD.
    est = estimate(
        n_runs=100,
        in_tokens=10_000,
        out_tokens=2_500,
        rung="R1",
        price_table=sample_price_table,
        cached_prefix_fraction=0.60,
    )
    assert est == 0.17


def test_no_confirm_performs_zero_calls(tmp_path, sample_price_table):
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = CostLedger(ledger_path=ledger_path, project_caps={"p01_baseline": 2.0})

    runner = SweepRunner(
        project="p01_baseline",
        price_table=sample_price_table,
        ledger=ledger,
        confirmed=False,  # NOT confirmed
    )

    call_count = 0

    def fake_paid_endpoint(task):
        nonlocal call_count
        call_count += 1
        raise AssertionError("Fake paid endpoint was called without --confirm!")

    tasks = ["task-1", "task-2", "task-3"]

    with pytest.raises(RuntimeError, match="requires explicit --confirm"):
        runner.execute_sweep(
            tasks=tasks,
            get_task_id=lambda t: t,
            call_fn=fake_paid_endpoint,
            in_tokens_est=1000,
            out_tokens_est=500,
            rung="R1",
        )

    # Assert ZERO paid calls occurred and ledger is empty
    assert call_count == 0
    assert not ledger_path.exists() or len(ledger.read_entries()) == 0


def test_budget_exceeded_halts_and_preserves_partial_results(tmp_path, sample_price_table):
    ledger_path = tmp_path / "ledger.jsonl"
    partial_path = tmp_path / "partial_results.json"

    # Set tight project cap of $0.0025
    ledger = CostLedger(
        ledger_path=ledger_path,
        project_caps={"p01_baseline": 0.0025},
    )

    runner = SweepRunner(
        project="p01_baseline",
        price_table=sample_price_table,
        ledger=ledger,
        confirmed=True,
    )

    # Each task costs $0.0010
    tasks = ["task-001", "task-002", "task-003", "task-004"]
    executed_tasks = []

    def mock_endpoint(task):
        executed_tasks.append(task)
        # 10,000 input ($0.001) + 0 output -> $0.001 per call
        usage = CallUsage(input_tokens=10_000, output_tokens=0, usd=0.0010)
        return {"answer": f"ans-{task}"}, True, usage

    with pytest.raises(BudgetExceeded):
        runner.execute_sweep(
            tasks=tasks,
            get_task_id=lambda t: t,
            call_fn=mock_endpoint,
            in_tokens_est=10_000,
            out_tokens_est=0,
            rung="R1",
            partial_output_path=partial_path,
        )

    # Task 1 costs $0.0010 -> total $0.0010 (under cap $0.0025) -> success
    # Task 2 costs $0.0010 -> total $0.0020 (under cap $0.0025) -> success
    # Task 3 costs $0.0010 -> total would be $0.0030 > $0.0025 -> cap exceeded!
    # Exactly 2 tasks completed
    assert len(executed_tasks) == 2

    # Verify ledger on disk has exactly 2 entries
    entries = ledger.read_entries("p01_baseline")
    assert len(entries) == 2
    assert ledger.spent("p01_baseline") == 0.0020

    # Verify partial results file is on disk and readable
    assert partial_path.exists()
    with open(partial_path, "r", encoding="utf-8") as f:
        partial_data = json.load(f)

    assert partial_data["completed_tasks"] == 2
    assert len(partial_data["results"]) == 2
    assert partial_data["results"][0]["task_id"] == "task-001"
    assert partial_data["results"][1]["task_id"] == "task-002"
    assert partial_data["halted_due_to_budget"] is True
