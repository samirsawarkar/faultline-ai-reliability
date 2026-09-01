import pytest
from faultline_p2.agent.contracts import ScenarioTask, OutcomeStatus, AgentOutcome
from faultline_p2.agent.agent import run_agent
from faultline_p2.agent.model import ModelResponse, StubModel

def get_env():
    return {"documents": []}

def get_task():
    return ScenarioTask(task_id="t-1", prompt="Hello?")

def test_termination_answer_produced():
    model = StubModel(explicit_responses=[ModelResponse(answer="42", cited_sources=["doc-0001"])])
    outcome = run_agent(get_task(), get_env(), model, step_cap=8)
    assert outcome.status == OutcomeStatus.ANSWERED
    assert outcome.answer == "42"

def test_termination_step_cap():
    responses = [ModelResponse(tool_call={"tool": "search", "query": "q"}) for _ in range(8)]
    model = StubModel(explicit_responses=responses)
    outcome = run_agent(get_task(), get_env(), model, step_cap=8)
    assert outcome.status == OutcomeStatus.STEP_CAP
    assert outcome.steps_used == 8

def test_termination_malformed_no_answer_no_tool():
    model = StubModel(explicit_responses=[ModelResponse(thought="thinking...")])
    outcome = run_agent(get_task(), get_env(), model, step_cap=8)
    assert outcome.status == OutcomeStatus.MALFORMED
    assert "missing answer and tool call" in outcome.reason

def test_termination_malformed_tool_call():
    model = StubModel(explicit_responses=[ModelResponse(tool_call={"tool": "unknown"})])
    outcome = run_agent(get_task(), get_env(), model, step_cap=8)
    assert outcome.status == OutcomeStatus.MALFORMED
    assert "Malformed tool call" in outcome.reason

def test_termination_model_failure():
    class FailingModel:
        def generate(self, messages):
            raise ValueError("API is down")
    
    outcome = run_agent(get_task(), get_env(), FailingModel(), step_cap=8)
    assert outcome.status == OutcomeStatus.MODEL_FAILURE
    assert "API is down" in outcome.reason

def test_termination_tool_error():
    class ErrorToolBox:
        def dispatch(self, call):
            raise RuntimeError("Database exploded")
    
    from faultline_p2.agent.agent import run_agent
    from faultline_p2.agent.contracts import OutcomeStatus
    
    import faultline_p2.agent.agent as agent_module
    old_toolbox = agent_module.ToolBox
    agent_module.ToolBox = lambda env: ErrorToolBox()
    
    model = StubModel(explicit_responses=[ModelResponse(tool_call={"tool": "search", "query": "q"})])
    try:
        outcome = run_agent(get_task(), get_env(), model, step_cap=8)
        assert outcome.status == OutcomeStatus.TOOL_ERROR
        assert "Database exploded" in outcome.reason
    finally:
        agent_module.ToolBox = old_toolbox
