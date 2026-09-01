import pytest
import sqlite3
import os
import subprocess
from pathlib import Path

def test_mid_sweep_crash(tmp_path):
    db_path = tmp_path / "trace.db"
    
    script = f"""
import sys
from faultline_p2.trace.store import TraceStore
store = TraceStore("{db_path}")
run_id = store.start_run()
store.log_span(run_id, "s-001", "T1", 1, "m1", "prov", "v1", tool_name="search")
store.log_span(run_id, "s-001", "T1", 2, "m1", "prov", "v1", termination_reason="model_failure")
sys.exit(1)
    """
    script_path = tmp_path / "run.py"
    script_path.write_text(script)
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent)
    
    subprocess.run(["python3", str(script_path)], env=env)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    spans = conn.execute("SELECT * FROM spans ORDER BY step_index").fetchall()
    conn.close()
    
    assert len(spans) == 2
    assert spans[0]["tool_name"] == "search"
    assert spans[1]["termination_reason"] == "model_failure"
    
