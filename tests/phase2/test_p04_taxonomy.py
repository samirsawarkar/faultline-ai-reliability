"""Tests for Project P4: Failure Taxonomy Tools."""
from __future__ import annotations

import csv
from pathlib import Path

from projects.p04_taxonomy.export_sheet import export_coding_sheet
from projects.p04_taxonomy.viewer import load_trace_data, render_trace_terminal
from faultline_p2.env.corpus import build_corpus


def test_p04_export_coding_sheet(tmp_path):
    trace_db = Path("projects/p03_grounding/trace.db")
    if not trace_db.exists():
        trace_db = Path("projects/p01_baseline/trace.db")

    csv_out = tmp_path / "coding_sheet.csv"
    md_out = tmp_path / "coding_sheet.md"

    count = export_coding_sheet(
        trace_db_path=trace_db,
        sweep_output_path=Path("projects/p03_grounding/sweep_output.json"),
        csv_out=csv_out,
        md_out=md_out,
    )

    assert count > 0
    assert csv_out.is_file()
    assert md_out.is_file()

    with open(csv_out, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == count
        assert "scenario_id" in rows[0]
        assert "open_coding_first_failure" in rows[0]


def test_p04_viewer_render():
    trace_db = Path("projects/p03_grounding/trace.db")
    if not trace_db.exists():
        trace_db = Path("projects/p01_baseline/trace.db")

    traces = load_trace_data(trace_db)
    assert len(traces) > 0

    corpus = build_corpus()
    scenario_map = {s.scenario_id: s for s in corpus.scenarios}

    first_sid = list(traces.keys())[0]
    output = render_trace_terminal(first_sid, traces[first_sid], scenario_map)

    assert first_sid in output
    assert "SCENARIO:" in output
    assert "Step 01" in output
