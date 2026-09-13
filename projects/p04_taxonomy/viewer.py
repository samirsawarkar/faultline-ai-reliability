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


def render_trace_terminal(
    scenario_id: str, 
    spans: List[sqlite3.Row], 
    scenario_map: Dict[str, Any],
    sweep_item: Optional[Dict[str, Any]] = None,
) -> str:
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
    
    if sweep_item and "output" in sweep_item:
        out = sweep_item["output"]
        if out.get("answer"):
            lines.append(f"Agent Answer:    {out.get('answer')}")
        if out.get("cited_sources"):
            lines.append(f"Cited Sources:   {', '.join(out.get('cited_sources'))}")
        if out.get("reason"):
            lines.append(f"Failure Reason:  {out.get('reason')}")
    lines.append("-" * 80)

    # Detailed trace from sweep_item if available
    trace_steps = (sweep_item or {}).get("output", {}).get("trace", [])
    step_dict = {t.get("index"): t for t in trace_steps}

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

        # Print tool details from sweep output if present
        step_info = step_dict.get(step_idx)
        if step_info:
            tc = step_info.get("tool_call") or {}
            obs = step_info.get("observation") or {}
            if tc:
                call_desc = f"        Call: {tc.get('tool', tool)}(" + ", ".join(f"{k}={v!r}" for k, v in tc.items() if k != "tool") + ")"
                lines.append(call_desc)
            if obs:
                if "candidates" in obs:
                    lines.append(f"        Result: {len(obs['candidates'])} candidates returned")
                elif "text" in obs:
                    snippet = obs["text"][:120] + ("..." if len(obs["text"]) > 120 else "")
                    lines.append(f"        Result: \"{snippet}\"")
                elif obs.get("error"):
                    lines.append(f"        Error: {obs.get('error')}")

    lines.append("=" * 80)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="P04 Trace Viewer Helper for Open Coding")
    parser.add_argument("--db", default="projects/p03_grounding/trace.db", help="Path to trace.db")
    parser.add_argument("--sweep", default="projects/p03_grounding/sweep_output.json", help="Path to sweep_output.json")
    parser.add_argument("--scenario", help="Inspect specific scenario ID (e.g., s-0042)")
    parser.add_argument("--doc", help="Inspect content of a document ID (e.g., doc-0098)")
    parser.add_argument("--tier", choices=["T1", "T2", "T3"], help="Filter by tier")
    parser.add_argument("--failed-only", action="store_true", help="Show only failed scenarios")
    parser.add_argument("--limit", type=int, default=10, help="Number of traces to display")
    args = parser.parse_args()

    corpus = build_corpus()
    if args.doc:
        doc = next((d for d in corpus.documents if (d.get("id") if isinstance(d, dict) else getattr(d, "id", None)) == args.doc), None)
        if doc:
            d_id = doc.get("id") if isinstance(doc, dict) else getattr(doc, "id", "")
            d_title = doc.get("title") if isinstance(doc, dict) else getattr(doc, "title", "")
            d_text = doc.get("text") if isinstance(doc, dict) else getattr(doc, "text", "")
            print("=" * 80)
            print(f"DOCUMENT ID:    {d_id}")
            print(f"DOCUMENT TITLE: {d_title}")
            print("-" * 80)
            print(d_text)
            print("=" * 80)
        else:
            print(f"Document '{args.doc}' not found in corpus.")
        return

    db_path = Path(args.db)
    if not db_path.exists():
        db_path = Path("projects/p01_baseline/trace.db")

    traces = load_trace_data(db_path)

    sweep_results: Dict[str, Any] = {}
    sweep_path = Path(args.sweep)
    if sweep_path.exists():
        try:
            with open(sweep_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data.get("results", []):
                    sweep_results[item["task_id"]] = item
        except Exception:
            pass

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
        print(render_trace_terminal(sid, traces[sid], scenario_map, sweep_results.get(sid)))
        print()


if __name__ == "__main__":
    main()
