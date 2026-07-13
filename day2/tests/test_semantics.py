"""Schema validity is not semantic correctness (the Day-2 learning goal), and
the agent is deterministic (the FAULTLINE house rule)."""
from conftest import entities

from faultline_agent import Agent, ArchiveSumTask, OutcomeStatus, load_env, verdict
from faultline_agent.contracts import AgentOutcome


def test_agent_is_deterministic():
    env = load_env(7)
    task_in = {"task_id": "det", "entities": entities(env, 4)}
    a = Agent(env).run(task_in).model_dump_json()
    b = Agent(env).run(task_in).model_dump_json()
    assert a == b


def test_schema_valid_but_semantically_wrong_answer_is_caught():
    """A perfectly well-formed AgentOutcome can still be WRONG. Pydantic passes
    it; the verdict must reject it. This is the crux of LEARN.md."""
    env = load_env(7)
    task_in = {"task_id": "sem", "entities": entities(env, 3)}
    task = ArchiveSumTask.model_validate(task_in)
    truth, required = __import__("faultline_agent").ground_truth(env, task)

    wrong = AgentOutcome(
        task_id="sem",
        status=OutcomeStatus.SOLVED,
        answer=str(truth + 1),                 # off by one — still a valid str
        cited_sources=sorted(required),
        steps_used=0, step_cap=12,
    )
    # It is schema-valid (constructing it did not raise)...
    assert isinstance(wrong, AgentOutcome)
    # ...but semantically wrong, and the verdict says so.
    v = verdict(env, task, wrong)
    assert v["correct"] is False and v["passed"] is False


def test_schema_valid_but_ungrounded_is_caught():
    env = load_env(7)
    task_in = {"task_id": "grnd", "entities": entities(env, 3)}
    task = ArchiveSumTask.model_validate(task_in)
    truth, _ = __import__("faultline_agent").ground_truth(env, task)

    right_number_no_sources = AgentOutcome(
        task_id="grnd", status=OutcomeStatus.SOLVED,
        answer=str(truth), cited_sources=[],   # correct number, cites nothing
        steps_used=0, step_cap=12,
    )
    v = verdict(env, task, right_number_no_sources)
    assert v["correct"] is True
    assert v["grounded"] is False and v["passed"] is False


def test_incomplete_outcome_never_passes_verdict():
    env = load_env(7)
    task_in = {"task_id": "inc", "entities": entities(env, 6)}  # over budget
    task = ArchiveSumTask.model_validate(task_in)
    out = Agent(env).run(task_in)
    v = verdict(env, task, out)
    assert out.status is OutcomeStatus.INCOMPLETE
    assert v["passed"] is False
