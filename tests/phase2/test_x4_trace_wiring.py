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
from faultline_p2.agent.agent import run_agent
from faultline_p2.agent.contracts import ScenarioTask
from faultline_p2.agent.model import ModelInterface, ModelResponse

class ExceptionModel(ModelInterface):
    def __init__(self):
        self.step = 0
        self.model_name = "test"
        self.provider = "test"
        self.version = "1"
        
    def generate(self, messages):
        self.step += 1
        if self.step == 1:
            return ModelResponse(tool_call={{"tool": "search", "query": "hello"}})
        else:
            raise RuntimeError("Out of memory error")
            
store = TraceStore("{db_path}")
run_id = store.start_run()
task = ScenarioTask(task_id="t-1", prompt="prompt", tier="T1")
env = {{"documents": []}}
run_agent(task, env, ExceptionModel(), trace_store=store, run_id=run_id, step_cap=12)
    """
    script_path = tmp_path / "run.py"
    script_path.write_text(script)
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent)
    
    subprocess.run([".venv/bin/python", str(script_path)], env=env)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    spans = conn.execute("SELECT * FROM spans ORDER BY step_index").fetchall()
    conn.close()
    
    assert len(spans) == 2
    assert spans[0]["tool_name"] == "search"
    assert spans[0]["termination_reason"] is None
    assert spans[1]["termination_reason"] == "model_failure"
