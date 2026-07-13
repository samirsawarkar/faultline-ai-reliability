"""Validation cannot be bypassed, and the outcome is always structured."""
import pytest
from conftest import entities
from pydantic import ValidationError

from faultline_agent import Agent, AgentOutcome, OutcomeStatus, load_env
from faultline_agent.contracts import (
    TOOL_CALL_ADAPTER,
    AgentStep,
    CalcCall,
    LookupCall,
    SearchCall,
    SearchResult,
)


def test_invalid_task_returns_structured_invalid_not_exception():
    env = load_env(7)
    # empty entity list violates min_length=1
    out = Agent(env).run({"task_id": "bad", "entities": []})
    assert isinstance(out, AgentOutcome)
    assert out.status is OutcomeStatus.INVALID
    assert out.answer is None


def test_unknown_field_in_task_is_rejected():
    env = load_env(7)
    out = Agent(env).run(
        {"task_id": "x", "entities": entities(env, 1), "sneaky": True}
    )
    assert out.status is OutcomeStatus.INVALID  # extra="forbid" caught it


def test_toolcall_adapter_rejects_bad_arguments():
    # missing required arg
    with pytest.raises(ValidationError):
        TOOL_CALL_ADAPTER.validate_python({"tool": "lookup"})
    # malformed doc_id (pattern)
    with pytest.raises(ValidationError):
        TOOL_CALL_ADAPTER.validate_python({"tool": "lookup", "doc_id": "nope"})
    # unknown tool
    with pytest.raises(ValidationError):
        TOOL_CALL_ADAPTER.validate_python({"tool": "delete_all", "x": 1})


def test_toolcall_adapter_accepts_valid_discriminated_input():
    call = TOOL_CALL_ADAPTER.validate_python({"tool": "search", "query": "Aster Labs"})
    assert isinstance(call, SearchCall)
    call = TOOL_CALL_ADAPTER.validate_python({"tool": "calc", "expression": "1+2"})
    assert isinstance(call, CalcCall)


def test_solved_outcome_without_answer_is_impossible():
    """The model invariant forbids a well-formed-but-lying SOLVED outcome."""
    with pytest.raises(ValidationError):
        AgentOutcome(
            task_id="t", status=OutcomeStatus.SOLVED, answer=None,
            steps_used=0, step_cap=12,
        )


def test_steps_used_cannot_exceed_cap():
    with pytest.raises(ValidationError):
        AgentOutcome(
            task_id="t", status=OutcomeStatus.INCOMPLETE,
            steps_used=13, step_cap=12,
        )


def test_outcome_is_json_roundtrippable():
    """Fully structured == serializes and re-validates byte-for-byte."""
    env = load_env(7)
    out = Agent(env).run({"task_id": "rt", "entities": entities(env, 3)})
    dumped = out.model_dump_json()
    back = AgentOutcome.model_validate_json(dumped)
    assert back.model_dump_json() == dumped
    # the trace is composed of typed steps, not raw dicts
    assert all(isinstance(s, AgentStep) for s in back.trace)
