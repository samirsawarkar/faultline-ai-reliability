"""Termination is the Day-2 gate: the agent must never hang and must always
return a structured outcome. These tests prove the loop is bounded and that an
over-budget task stops cleanly as INCOMPLETE."""
from conftest import entities

from faultline_agent import Agent, AgentOutcome, OutcomeStatus, load_env, verdict
from faultline_agent import ArchiveSumTask

STEP_CAP = 12


def test_every_task_returns_an_agentoutcome_within_cap():
    env = load_env(7)
    names = entities(env)
    # Sweep task sizes on both sides of the budget boundary (2k+1 vs cap=12).
    for k in range(1, len(names) + 1):
        out = Agent(env, step_cap=STEP_CAP).run(
            {"task_id": f"t-{k}", "entities": names[:k]}
        )
        assert isinstance(out, AgentOutcome)
        assert 0 <= out.steps_used <= STEP_CAP
        assert len(out.trace) == out.steps_used


def test_solvable_task_is_solved_and_grounded():
    env = load_env(7)
    task_in = {"task_id": "t-solve", "entities": entities(env, 4)}  # 9 steps
    out = Agent(env, step_cap=STEP_CAP).run(task_in)
    assert out.status is OutcomeStatus.SOLVED
    assert out.answer is not None
    v = verdict(env, ArchiveSumTask.model_validate(task_in), out)
    assert v["passed"] is True


def test_over_budget_task_terminates_incomplete_not_hang():
    env = load_env(7)
    # 6 entities -> 2*6+1 = 13 steps demanded, cap is 12: must stop clean.
    task_in = {"task_id": "t-over", "entities": entities(env, 6)}
    out = Agent(env, step_cap=STEP_CAP).run(task_in)
    assert out.status is OutcomeStatus.INCOMPLETE
    assert out.answer is None                 # honest: no fabricated answer
    assert out.steps_used == STEP_CAP         # spent exactly the budget
    assert out.reason and "step cap" in out.reason


def test_budget_boundary_is_exactly_where_expected():
    env = load_env(7)
    names = entities(env)
    # k=5 -> 11 steps -> SOLVED; k=6 -> 13 steps -> INCOMPLETE.
    solved = Agent(env, step_cap=STEP_CAP).run({"task_id": "b5", "entities": names[:5]})
    over = Agent(env, step_cap=STEP_CAP).run({"task_id": "b6", "entities": names[:6]})
    assert solved.status is OutcomeStatus.SOLVED and solved.steps_used == 11
    assert over.status is OutcomeStatus.INCOMPLETE and over.steps_used == 12


def test_tiny_cap_still_terminates_cleanly():
    """Even a cap so small nothing can finish must not hang or raise."""
    env = load_env(3)
    out = Agent(env, step_cap=1).run({"task_id": "t-1", "entities": entities(env, 2)})
    assert out.status is OutcomeStatus.INCOMPLETE
    assert out.steps_used == 1
