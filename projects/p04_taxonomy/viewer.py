"""P04 Trace Viewer Helper for Human Open Coding.

Provides an interactive and CLI interface for inspecting full multi-step
execution traces from P3 grounding runs to support open and axial failure coding.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from faultline_p2.env.corpus import build_corpus


def load_trace_data(db_path: Path, run_id: Optional[str] = None) -> Dict[str, List[sqlite3.Row]]:
    """Load and group all spans by scenario_id from trace.db."""
    if not db_path.exists():
        raise FileNotFoundError(f"Trace database not found at {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    if run_id is None:
        row = conn.execute("SELECT run_id FROM runs ORDER BY start_time DESC, rowid DESC LIMIT 1").fetchone()
        if row is None:
            row = conn.execute("SELECT run_id FROM spans ORDER BY rowid DESC LIMIT 1").fetchone()
        if row is None:
            raise ValueError(f"No runs found in {db_path}")
        run_id = row["run_id"]

    spans = conn.execute(
        """
        SELECT * FROM spans 
        WHERE run_id = ? 
        ORDER BY scenario_id, step_index ASC, timestamp ASC
        """,
        (run_id,),
    ).fetchall()

    grouped: Dict[str, List[sqlite3.Row]] = {}
    for s in spans:
        sc_id = s["scenario_id"]
        grouped.setdefault(sc_id, []).append(s)

    conn.close()
    return grouped


def render_trace_terminal(scenario_id: str, spans: List[sqlite3.Row], scenario_map: Dict[str, Any]) -> str:
    """Render a human-readable, detailed terminal view of a single scenario execution trace."""
    sc = scenario_map.get(scenario_id)
    lines = []
    lines.append("=" * 80)
    tier = spans[0]["tier"] if spans else (sc.tier if sc else "Unknown")
    verdict = spans[-1]["verdict"] if spans else 0
    verdict_str = "PASS" if verdict == 1 else "FAIL"

    lines.append(f"SCENARIO: {scenario_id} [{tier}]  |  VERDICT: {verdict_str}  |  STEPS: {len(spans)}")
    if sc:
        lines.append(f"Prompt:          {sc.prompt}")
        lines.append(f"Expected Answer: {sc.final_answer}")
        lines.append(f"Required Source: {sc.required_source}")
        if hasattr(sc, "traversal_sources") and sc.traversal_sources:
            lines.append(f"Traversal Path:  {' -> '.join(sc.traversal_sources)}")
    lines.append("-" * 80)

    for s in spans:
        step_idx = s["step_index"]
        tool = s["tool_name"] or "reasoning"
        reason = s["termination_reason"] or ""
        tokens_p = s["prompt_tokens"]
        tokens_c = s["completion_tokens"]
        lat = s["latency_ms"]

        header = f"Step {step_idx:02d} | Tool: {tool:<10} | Tokens: (in={tokens_p}, out={tokens_c}) | Latency: {lat:.0f}ms"
        if reason:
            header += f" | Termination: {reason}"
        lines.append(header)

    lines.append("=" * 80)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="P04 Trace Viewer Helper for Open Coding")
    parser.add_argument("--db", default="projects/p03_grounding/trace.db", help="Path to trace.db")
    parser.add_argument("--scenario", help="Inspect specific scenario ID (e.g., s-0042)")
    parser.add_argument("--tier", choices=["T1", "T2", "T3"], help="Filter by tier")
    parser.add_argument("--failed-only", action="store_true", help="Show only failed scenarios")
    parser.add_argument("--limit", type=int, default=10, help="Number of traces to display")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        # Fallback to P1 trace if P3 not available
        db_path = Path("projects/p01_baseline/trace.db")

    traces = load_trace_data(db_path)
    corpus = build_corpus()
    scenario_map = {s.scenario_id: s for s in corpus.scenarios}

    selected_ids = list(traces.keys())

    if args.scenario:
        selected_ids = [args.scenario] if args.scenario in traces else []
    else:
        if args.tier:
            selected_ids = [
                sid for sid in selected_ids if traces[sid] and traces[sid][0]["tier"] == args.tier
            ]
        if args.failed_only:
            selected_ids = [
                sid for sid in selected_ids if traces[sid] and traces[sid][-1]["verdict"] != 1
            ]

    print(f"Loaded {len(traces)} total traces. Showing {min(len(selected_ids), args.limit)} matching traces:")
    for sid in selected_ids[: args.limit]:
        print(render_trace_terminal(sid, traces[sid], scenario_map))
        print()


if __name__ == "__main__":
    main()
