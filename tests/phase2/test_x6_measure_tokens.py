import pytest
from faultline_p2.env.corpus import build_corpus
from faultline_p2.agent.model import StubModel
from faultline_p2.agent.agent import run_agent, count_tokens
from faultline_p2.agent.contracts import ScenarioTask, OutcomeStatus

def test_measure_tokens():
    corpus = build_corpus()
    env = {"documents": corpus.documents}
    model = StubModel(behavior="solver")
    
    tier_tokens = {"T1": {"prompt": 0, "completion": 0, "runs": 0}, 
                   "T2": {"prompt": 0, "completion": 0, "runs": 0}, 
                   "T3": {"prompt": 0, "completion": 0, "runs": 0}}
    
    # We will simulate the tokens by summing the tokens of messages at each generate call.
    # But wait, run_agent already calculates tokens! But they are only logged in TraceStore.
    # Let's use TraceStore in memory!
    import sqlite3
    from faultline_p2.trace.store import TraceStore
    
    store = TraceStore(":memory:")
    run_id = store.start_run()
    
    for sc in corpus.scenarios:
        task = ScenarioTask(task_id=sc.scenario_id, prompt=sc.prompt, tier=sc.tier)
        outcome = run_agent(task, env, model, step_cap=12, trace_store=store, run_id=run_id)
        assert outcome.status == OutcomeStatus.ANSWERED
        
    conn = sqlite3.connect(":memory:")
    # We can just fetch from the store's connection
    spans = store.conn.execute("SELECT tier, SUM(prompt_tokens) as p, SUM(completion_tokens) as c, COUNT(DISTINCT scenario_id) as n FROM spans GROUP BY tier").fetchall()
    
    print("\nTokens per run by tier:")
    for row in spans:
        tier, p, c, n = row["tier"], row["p"], row["c"], row["n"]
        print(f"{tier}: ~{int(p/n)} prompt / ~{int(c/n)} completion")

