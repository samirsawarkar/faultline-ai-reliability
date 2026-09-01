import pytest
from faultline_p2.env.corpus import build_corpus
from faultline_p2.oracle import oracle_check
from faultline_p2.agent.model import StubModel
from faultline_p2.agent.agent import run_agent
from faultline_p2.agent.contracts import ScenarioTask, OutcomeStatus

def test_oracle_wiring_correct_but_wrong_citation_fails():
    corpus = build_corpus(seed=42)
    sc = corpus.scenarios[0]
    
    # We use a T2 or T3 scenario so there are link docs
    t2_sc = next(s for s in corpus.scenarios if s.tier in ("T2", "T3"))
    
    task = ScenarioTask(task_id=t2_sc.scenario_id, prompt=t2_sc.prompt)
    env = {"documents": corpus.documents}
    
    model = StubModel(behavior="correct_wrong_citation", scenarios=[t2_sc])
    outcome = run_agent(task, env, model, step_cap=8)
    
    assert outcome.status == OutcomeStatus.SOLVED
    assert outcome.answer == t2_sc.final_answer
    
    # ensure citation is wrong (e.g. it's a link doc)
    assert t2_sc.required_source not in outcome.cited_sources
    assert any(c.startswith("link-") for c in outcome.cited_sources)
    
    question = {
        "id": t2_sc.scenario_id,
        "answer": t2_sc.final_answer,
        "required_source": t2_sc.required_source
    }
    response = {
        "answer": outcome.answer,
        "cited_sources": outcome.cited_sources
    }
    
    verdict = oracle_check(question, response)
    
    assert verdict["correct"] is True
    assert verdict["cited_required"] is False
    assert verdict["passed"] is False

def test_oracle_wiring_passes_when_grounded():
    corpus = build_corpus(seed=42)
    sc = corpus.scenarios[0]
    
    task = ScenarioTask(task_id=sc.scenario_id, prompt=sc.prompt)
    env = {"documents": corpus.documents}
    
    model = StubModel(behavior="correct", scenarios=[sc])
    outcome = run_agent(task, env, model, step_cap=8)
    
    question = {
        "id": sc.scenario_id,
        "answer": sc.final_answer,
        "required_source": sc.required_source
    }
    response = {
        "answer": outcome.answer,
        "cited_sources": outcome.cited_sources
    }
    
    verdict = oracle_check(question, response)
    
    assert verdict["correct"] is True
    assert verdict["cited_required"] is True
    assert verdict["passed"] is True
