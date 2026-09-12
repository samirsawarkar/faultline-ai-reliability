"""TraceStore SLI and SLO evaluation engine."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml

from .burn_rate import evaluate_burn_rate_alert, AlertEvaluation, compute_burn_rate


def _get_conn(db_or_conn: Union[str, Path, sqlite3.Connection]) -> tuple[sqlite3.Connection, bool]:
    if isinstance(db_or_conn, (str, Path)):
        conn = sqlite3.connect(str(db_or_conn))
        conn.row_factory = sqlite3.Row
        return conn, True
    return db_or_conn, False


def get_latest_run_id(conn: sqlite3.Connection) -> Optional[str]:
    """Retrieve the most recent run_id from runs or spans."""
    row = conn.execute("SELECT run_id FROM runs ORDER BY start_time DESC, rowid DESC LIMIT 1").fetchone()
    if row:
        return row["run_id"]
    row_span = conn.execute("SELECT run_id FROM spans ORDER BY rowid DESC LIMIT 1").fetchone()
    if row_span:
        return row_span["run_id"]
    return None


def evaluate_grounded_pass_rate_sli(
    db_or_conn: Union[str, Path, sqlite3.Connection],
    run_id: Optional[str] = None
) -> Dict[str, Any]:
    """Calculate grounded pass rate SLI from trace.db."""
    conn, should_close = _get_conn(db_or_conn)
    try:
        if run_id is None:
            run_id = get_latest_run_id(conn)
        if run_id is None:
            return {"total_scenarios": 0, "passed_scenarios": 0, "pass_rate": 0.0, "error_rate": 0.0}

        rows = conn.execute("""
            SELECT scenario_id, MAX(COALESCE(verdict, 0)) as passed
            FROM spans
            WHERE run_id = ?
            GROUP BY scenario_id
        """, (run_id,)).fetchall()

        total = len(rows)
        passed = sum(1 for r in rows if r["passed"] == 1)
        pass_rate = round(passed / total, 4) if total > 0 else 0.0
        error_rate = round(1.0 - pass_rate, 4) if total > 0 else 0.0

        return {
            "total_scenarios": total,
            "passed_scenarios": passed,
            "pass_rate": pass_rate,
            "error_rate": error_rate,
            "run_id": run_id
        }
    finally:
        if should_close:
            conn.close()


def evaluate_agent_error_rate_sli(
    db_or_conn: Union[str, Path, sqlite3.Connection],
    run_id: Optional[str] = None
) -> Dict[str, Any]:
    """Calculate agent infrastructure crash/malformed/error rate SLI from trace.db."""
    conn, should_close = _get_conn(db_or_conn)
    try:
        if run_id is None:
            run_id = get_latest_run_id(conn)
        if run_id is None:
            return {"total_scenarios": 0, "error_scenarios": 0, "error_rate": 0.0, "availability_rate": 1.0}

        rows = conn.execute("""
            SELECT scenario_id,
                   MAX(CASE WHEN termination_reason IN ('MODEL_FAILURE', 'TOOL_ERROR', 'MALFORMED') THEN 1 ELSE 0 END) as is_err
            FROM spans
            WHERE run_id = ?
            GROUP BY scenario_id
        """, (run_id,)).fetchall()

        total = len(rows)
        errors = sum(1 for r in rows if r["is_err"] == 1)
        error_rate = round(errors / total, 4) if total > 0 else 0.0
        avail_rate = round(1.0 - error_rate, 4) if total > 0 else 1.0

        return {
            "total_scenarios": total,
            "error_scenarios": errors,
            "error_rate": error_rate,
            "availability_rate": avail_rate,
            "run_id": run_id
        }
    finally:
        if should_close:
            conn.close()


def evaluate_step_latency_sli(
    db_or_conn: Union[str, Path, sqlite3.Connection],
    run_id: Optional[str] = None,
    threshold_ms: float = 1000.0
) -> Dict[str, Any]:
    """Calculate step latency percentile and breach rate SLI from trace.db."""
    conn, should_close = _get_conn(db_or_conn)
    try:
        if run_id is None:
            run_id = get_latest_run_id(conn)
        if run_id is None:
            return {"total_spans": 0, "p50_ms": 0.0, "p95_ms": 0.0, "error_rate": 0.0}

        rows = conn.execute("""
            SELECT latency_ms
            FROM spans
            WHERE run_id = ? AND latency_ms IS NOT NULL
            ORDER BY latency_ms ASC
        """, (run_id,)).fetchall()

        total = len(rows)
        if total == 0:
            return {"total_spans": 0, "p50_ms": 0.0, "p95_ms": 0.0, "error_rate": 0.0}

        latencies = [float(r["latency_ms"]) for r in rows]
        idx_p50 = int(total * 0.50)
        idx_p95 = min(int(total * 0.95), total - 1)
        p50 = latencies[idx_p50]
        p95 = latencies[idx_p95]

        slow_count = sum(1 for lat in latencies if lat > threshold_ms)
        error_rate = round(slow_count / total, 4)
        success_rate = round(1.0 - error_rate, 4)

        return {
            "total_spans": total,
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "threshold_ms": threshold_ms,
            "slow_spans": slow_count,
            "error_rate": error_rate,
            "success_rate": success_rate,
            "run_id": run_id
        }
    finally:
        if should_close:
            conn.close()


def evaluate_slos_from_trace(
    db_or_conn: Union[str, Path, sqlite3.Connection],
    slo_yaml_path: Union[str, Path] = "projects/p13_slo_incident/slo.yaml",
    run_id: Optional[str] = None
) -> Dict[str, Any]:
    """Evaluate all defined SLOs in slo.yaml against trace store."""
    with open(slo_yaml_path, "r") as f:
        config = yaml.safe_load(f)

    compliance_hours = float(config.get("compliance_period_hours", 720.0))
    results: Dict[str, Any] = {
        "service": config.get("service"),
        "compliance_period_hours": compliance_hours,
        "run_id": run_id,
        "slos": {},
        "overall_status": "ok"
    }

    conn, should_close = _get_conn(db_or_conn)
    try:
        if run_id is None:
            run_id = get_latest_run_id(conn)
        results["run_id"] = run_id

        for slo in config.get("slos", []):
            slo_id = slo["id"]
            target = float(slo["target"])
            error_budget = float(slo["error_budget"])
            fast_thresh = float(slo["alert_rules"]["fast_burn"]["burn_rate_threshold"])
            slow_thresh = float(slo["alert_rules"]["slow_burn"]["burn_rate_threshold"])
            short_win = float(slo["windows"]["short_window_hours"])
            long_win = float(slo["windows"]["long_window_hours"])

            if slo_id == "grounded_pass_rate":
                sli_data = evaluate_grounded_pass_rate_sli(conn, run_id)
                observed_error = sli_data["error_rate"]
            elif slo_id == "agent_error_rate":
                sli_data = evaluate_agent_error_rate_sli(conn, run_id)
                observed_error = sli_data["error_rate"]
            elif slo_id == "step_latency_p95":
                thresh_ms = float(slo.get("threshold_latency_ms", 1000.0))
                sli_data = evaluate_step_latency_sli(conn, run_id, thresh_ms)
                observed_error = sli_data["error_rate"]
            else:
                continue

            alert_eval = evaluate_burn_rate_alert(
                slo_id=slo_id,
                error_rate=observed_error,
                error_budget=error_budget,
                fast_burn_threshold=fast_thresh,
                slow_burn_threshold=slow_thresh,
                short_window_hours=short_win,
                long_window_hours=long_win,
                compliance_period_hours=compliance_hours
            )

            results["slos"][slo_id] = {
                "name": slo["name"],
                "target": target,
                "error_budget": error_budget,
                "sli_metrics": sli_data,
                "burn_rate": alert_eval.burn_rate,
                "fast_burn_fired": alert_eval.fast_burn_fired,
                "slow_burn_fired": alert_eval.slow_burn_fired,
                "severity": alert_eval.severity,
                "short_window_budget_consumed_pct": alert_eval.short_window_budget_consumed_pct,
                "long_window_budget_consumed_pct": alert_eval.long_window_budget_consumed_pct,
                "message": alert_eval.message
            }

            if alert_eval.severity == "page":
                results["overall_status"] = "page"
            elif alert_eval.severity == "ticket" and results["overall_status"] != "page":
                results["overall_status"] = "ticket"

        return results
    finally:
        if should_close:
            conn.close()
