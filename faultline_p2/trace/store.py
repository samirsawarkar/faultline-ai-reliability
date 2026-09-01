import sqlite3
import datetime
import uuid
from typing import Optional
from .schema_sql import SCHEMA

class TraceStore:
    def __init__(self, path: str = ":memory:"):
        self.conn = sqlite3.connect(path, isolation_level=None) # autocommit
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        
    def close(self):
        self.conn.close()
        
    def start_run(self) -> str:
        run_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow().isoformat()
        self.conn.execute("INSERT INTO runs (run_id, start_time, status) VALUES (?, ?, ?)", 
                          (run_id, now, "running"))
        return run_id
        
    def end_run(self, run_id: str, status: str):
        now = datetime.datetime.utcnow().isoformat()
        self.conn.execute("UPDATE runs SET end_time = ?, status = ? WHERE run_id = ?", 
                          (now, status, run_id))
                          
    def log_span(self, run_id: str, scenario_id: str, tier: str, step_index: int, 
                 model_name: str, provider: str, model_version: str,
                 tool_name: Optional[str] = None, quantization: Optional[str] = None,
                 prompt_tokens: int = 0, completion_tokens: int = 0, latency_ms: float = 0.0,
                 termination_reason: Optional[str] = None):
        span_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow().isoformat()
        self.conn.execute("""
            INSERT INTO spans (span_id, run_id, scenario_id, tier, step_index, tool_name,
                               model_name, provider, model_version, quantization,
                               prompt_tokens, completion_tokens, latency_ms,
                               termination_reason, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (span_id, run_id, scenario_id, tier, step_index, tool_name, model_name,
              provider, model_version, quantization, prompt_tokens, completion_tokens,
              latency_ms, termination_reason, now))
