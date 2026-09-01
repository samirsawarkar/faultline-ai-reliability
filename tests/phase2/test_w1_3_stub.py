import pytest
import socket
from faultline_p2.env.corpus import build_corpus
from faultline_p2.agent.model import StubModel
from faultline_p2.agent.agent import run_agent
from faultline_p2.agent.contracts import ScenarioTask, OutcomeStatus

def test_all_350_scenarios_offline(monkeypatch):
    # Patch socket to guarantee no network
    def block_socket(*args, **kwargs):
        raise RuntimeError("Network call attempted!")
    monkeypatch.setattr(socket, "socket", block_socket)
    
    corpus = build_corpus(seed=42)
    assert corpus.scenario_count == 350
    
    # Environment dict expected by ToolBox
    env = {"documents": corpus.documents}
    
    # Run the stub model with behavior="correct"
    model = StubModel(behavior="correct", scenarios=corpus.scenarios)
    
    success_count = 0
    for sc in corpus.scenarios:
        task = ScenarioTask(task_id=sc.scenario_id, prompt=sc.prompt)
        outcome = run_agent(task, env, model, step_cap=8)
        assert outcome.status == OutcomeStatus.SOLVED
        assert outcome.answer == sc.final_answer
        assert sc.required_source in outcome.cited_sources
        success_count += 1
        
    assert success_count == 350

def test_stub_behaviors():
    corpus = build_corpus(seed=42)
    sc = corpus.scenarios[0]
    task = ScenarioTask(task_id=sc.scenario_id, prompt=sc.prompt)
    env = {"documents": corpus.documents}
    
    # Correct but wrong citation
    model_wrong_cite = StubModel(behavior="correct_wrong_citation", scenarios=[sc])
    out1 = run_agent(task, env, model_wrong_cite, step_cap=8)
    assert out1.status == OutcomeStatus.SOLVED
    assert out1.answer == sc.final_answer
    assert sc.required_source not in out1.cited_sources
    
    # Wrong answer
    model_wrong_ans = StubModel(behavior="wrong_answer", scenarios=[sc])
    out2 = run_agent(task, env, model_wrong_ans, step_cap=8)
    assert out2.status == OutcomeStatus.SOLVED
    assert out2.answer != sc.final_answer
    
    # Malformed
    model_malformed = StubModel(behavior="malformed", scenarios=[sc])
    out3 = run_agent(task, env, model_malformed, step_cap=8)
    assert out3.status == OutcomeStatus.MALFORMED
    
    # Hard failure
    model_fail = StubModel(behavior="hard_failure", scenarios=[sc])
    out4 = run_agent(task, env, model_fail, step_cap=8)
    assert out4.status == OutcomeStatus.MODEL_FAILURE
    
    # Step cap
    model_cap = StubModel(behavior="step_cap", scenarios=[sc])
    out5 = run_agent(task, env, model_cap, step_cap=8)
    assert out5.status == OutcomeStatus.STEP_CAP

