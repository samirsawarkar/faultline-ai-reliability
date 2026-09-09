"""Export P3 Traces to Structured Open Coding Sheet.

Generates a spreadsheet (CSV) and Markdown document containing full scenario details,
agent outputs, citations, step counts, and blank taxonomy coding columns for human open coding.
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from faultline_p2.env.corpus import build_corpus


def export_coding_sheet(
    trace_db_path: Path,
    sweep_output_path: Optional[Path],
    csv_out: Path,
    md_out: Path,
) -> int:
    corpus = build_corpus()
    scenario_map = {s.scenario_id: s for s in corpus.scenarios}

    # Load from sweep_output.json if available
    sweep_results: Dict[str, Any] = {}
    if sweep_output_path and sweep_output_path.exists():
        with open(sweep_output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data.get("results", []):
                sweep_results[item["task_id"]] = item

    # Load from trace.db
    conn = sqlite3.connect(str(trace_db_path))
    conn.row_factory = sqlite3.Row

    row = conn.execute("SELECT run_id FROM runs ORDER BY start_time DESC, rowid DESC LIMIT 1").fetchone()
    if row is None:
        row = conn.execute("SELECT run_id FROM spans ORDER BY rowid DESC LIMIT 1").fetchone()
    run_id = row["run_id"] if row else None

    scenarios = conn.execute(
        """
        SELECT scenario_id, tier, 
               MAX(step_index) as steps, 
               SUM(prompt_tokens) as p_tokens, 
               SUM(completion_tokens) as c_tokens,
               MAX(COALESCE(verdict, 0)) as passed
        FROM spans
        WHERE run_id = ?
        GROUP BY scenario_id, tier
        ORDER BY tier ASC, scenario_id ASC
        """,
        (run_id,),
    ).fetchall()
    conn.close()

    rows: List[Dict[str, Any]] = []
    for s in scenarios:
        sid = s["scenario_id"]
        sc = scenario_map.get(sid)
        sweep_item = sweep_results.get(sid, {})
        output_obj = sweep_item.get("output", {})

        ans = output_obj.get("answer", "") if isinstance(output_obj, dict) else ""
        cited = output_obj.get("cited_sources", []) if isinstance(output_obj, dict) else []
        status = output_obj.get("status", "") if isinstance(output_obj, dict) else ""
        reason = output_obj.get("reason", "") if isinstance(output_obj, dict) else ""

        rows.append({
            "scenario_id": sid,
            "tier": s["tier"],
            "verdict": "PASS" if s["passed"] == 1 else "FAIL",
            "status": status,
            "steps_used": s["steps"],
            "prompt": sc.prompt if sc else "",
            "expected_answer": sc.final_answer if sc else "",
            "agent_answer": ans,
            "required_source": sc.required_source if sc else "",
            "cited_sources": "; ".join(cited),
            "reason_summary": reason,
            "open_coding_first_failure": "",
            "axial_failure_mode": "",
            "coding_notes": "",
        })

    # Write CSV
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_out, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "scenario_id",
            "tier",
            "verdict",
            "status",
            "steps_used",
            "prompt",
            "expected_answer",
            "agent_answer",
            "required_source",
            "cited_sources",
            "reason_summary",
            "open_coding_first_failure",
            "axial_failure_mode",
            "coding_notes",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Write Markdown Coding Sheet
    with open(md_out, "w", encoding="utf-8") as f:
        f.write("# P4 Failure Taxonomy — Open Coding Sheet\n\n")
        f.write(f"Total traces exported: **{len(rows)}**\n\n")
        f.write("| ID | Tier | Verdict | Steps | Expected Answer | Agent Answer | Required Source | Cited Sources | First Failure (Plain Language) | Axial Mode |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write(
                f"| `{r['scenario_id']}` | {r['tier']} | **{r['verdict']}** | {r['steps_used']} | "
                f"`{r['expected_answer']}` | `{r['agent_answer']}` | `{r['required_source']}` | `{r['cited_sources']}` | | |\n"
            )

    return len(rows)


def main():
    parser = argparse.ArgumentParser(description="Export P3 Traces for P4 Human Open Coding")
    parser.add_argument("--db", default="projects/p03_grounding/trace.db", help="Path to trace.db")
    parser.add_argument("--output-json", default="projects/p03_grounding/sweep_output.json", help="Path to sweep_output.json")
    parser.add_argument("--csv-out", default="projects/p04_taxonomy/coding_sheet.csv", help="CSV export destination")
    parser.add_argument("--md-out", default="projects/p04_taxonomy/coding_sheet.md", help="Markdown export destination")
    args = parser.parse_args()

    count = export_coding_sheet(
        trace_db_path=Path(args.db),
        sweep_output_path=Path(args.output_json),
        csv_out=Path(args.csv_out),
        md_out=Path(args.md_out),
    )
    print(f"Exported {count} scenario traces to {args.csv_out} and {args.md_out}")


if __name__ == "__main__":
    main()
