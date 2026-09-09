import datetime
import sqlite3
import threading
import uuid
from typing import Optional
from .schema_sql import SCHEMA


class TraceStore:
    def __init__(self, path: str = ":memory:"):
        self._lock = threading.RLock()
        with self._lock:
            self.conn = sqlite3.connect(
                path,
                isolation_level=None,  # autocommit
                check_same_thread=False,
                timeout=60.0,
            )
            self.conn.row_factory = sqlite3.Row
            if path != ":memory:":
                try:
                    self.conn.execute("PRAGMA journal_mode=WAL;")
                except Exception:
                    pass
            try:
                self.conn.execute("PRAGMA busy_timeout=60000;")
            except Exception:
                pass
            self.conn.executescript(SCHEMA)
            cols = [r[1] for r in self.conn.execute("PRAGMA table_info(spans)").fetchall()]
            if "verdict" not in cols:
                self.conn.execute("ALTER TABLE spans ADD COLUMN verdict INTEGER")

    def close(self):
        with self._lock:
            self.conn.close()

    def start_run(self, run_id: Optional[str] = None) -> str:
        if run_id is None:
            run_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow().isoformat()
        with self._lock:
            self.conn.execute(
                "INSERT INTO runs (run_id, start_time, status) VALUES (?, ?, ?)",
                (run_id, now, "running"),
            )
        return run_id

    def end_run(self, run_id: str, status: str):
        now = datetime.datetime.utcnow().isoformat()
        with self._lock:
            self.conn.execute(
                "UPDATE runs SET end_time = ?, status = ? WHERE run_id = ?",
                (now, status, run_id),
            )

    def record_verdict(self, run_id: str, scenario_id: str, verdict: bool | int):
        val = 1 if verdict else 0
        with self._lock:
            self.conn.execute(
                "UPDATE spans SET verdict = ? WHERE run_id = ? AND scenario_id = ?",
                (val, run_id, scenario_id),
            )

    def log_policy_decision(self, run_id: Optional[str], tool_name: str, allowed: bool, rule: str, reason: str):
        decision_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow().isoformat()
        with self._lock:
            self.conn.execute(
                """
                INSERT INTO policy_decisions (decision_id, run_id, tool_name, allowed, rule, reason, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (decision_id, run_id, tool_name, 1 if allowed else 0, rule, reason, now),
            )

    def log_span(
        self,
        run_id: str,
        scenario_id: str,
        tier: str,
        step_index: int,
        model_name: str,
        provider: str,
        model_version: str,
        tool_name: Optional[str] = None,
        quantization: Optional[str] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: float = 0.0,
        termination_reason: Optional[str] = None,
        verdict: Optional[int] = None,
    ):
        span_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow().isoformat()
        with self._lock:
            self.conn.execute(
                """
                INSERT INTO spans (span_id, run_id, scenario_id, tier, step_index, tool_name,
                                   model_name, provider, model_version, quantization,
                                   prompt_tokens, completion_tokens, latency_ms,
                                   termination_reason, timestamp, verdict)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    span_id,
                    run_id,
                    scenario_id,
                    tier,
                    step_index,
                    tool_name,
                    model_name,
                    provider,
                    model_version,
                    quantization,
                    prompt_tokens,
                    completion_tokens,
                    latency_ms,
                    termination_reason,
                    now,
                    verdict,
                ),
            )

