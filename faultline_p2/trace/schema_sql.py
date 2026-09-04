SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    start_time TEXT,
    end_time TEXT,
    status TEXT
);

CREATE TABLE IF NOT EXISTS spans (
    span_id TEXT PRIMARY KEY,
    run_id TEXT,
    scenario_id TEXT,
    tier TEXT,
    step_index INTEGER,
    tool_name TEXT,
    model_name TEXT,
    provider TEXT,
    model_version TEXT,
    quantization TEXT,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    latency_ms REAL,
    termination_reason TEXT,
    timestamp TEXT,
    verdict INTEGER
);
"""
