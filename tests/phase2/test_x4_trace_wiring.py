import pytest
import subprocess
import sqlite3
import os
import sys
from faultline_p2.env.corpus import build_corpus
from faultline_p2.trace.store import TraceStore

def test_trace_durability_hard_kill(tmp_path):
    db_path = str(tmp_path / "trace.db")
    
    script = f"""
import sys
import os
from faultline_p2.env.corpus import build_corpus
from faultline_p2.agent.model import StubModel
from faultline_p2.agent.agent import run_agent
from faultline_p2.agent.contracts import ScenarioTask
from faultline_p2.trace.store import TraceStore

# Use os._exit in the model to simulate a hard kill
class HardKillModel(StubModel):
    def __init__(self):
        super().__init__(behavior="solver")
        self.calls = 0
    def generate(self, messages):
        self.calls += 1
        if self.calls == 2:
            import os
            os._exit(9)
        return super().generate(messages)

store = TraceStore("{db_path}")
run_id = store.start_run()
corpus = build_corpus()
sc = corpus.scenarios[0]
env = {{"documents": corpus.documents}}

task = ScenarioTask(task_id=sc.scenario_id, prompt=sc.prompt)
run_agent(task, env, HardKillModel(), step_cap=12, trace_store=store, run_id=run_id)
"""
    script_path = str(tmp_path / "run_kill.py")
    with open(script_path, "w") as f:
        f.write(script)
        
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    result = subprocess.run([sys.executable, script_path], env=env)
    
    # Assert it exited with code 9
    assert result.returncode == 9
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    runs = conn.execute("SELECT * FROM runs").fetchall()
    assert len(runs) == 1
    
    # It should have written the first step span before the crash
    spans = conn.execute("SELECT * FROM spans").fetchall()
    assert len(spans) > 0
    assert spans[0]["tool_name"] == "search"
