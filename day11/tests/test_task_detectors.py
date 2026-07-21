"""The task model and the F5/F6 detectors."""
from __future__ import annotations

from faultline_spectrum import (
    EXPECTED_CONTEXT,
    EXPECTED_FINAL,
    M_STEPS,
    STEP_BUDGET,
    budget_detect,
    context_integrity_detect,
    is_correct,
    loop_detect,
    repetition_detect,
    run_task,
)


def test_clean_run_is_correct_and_undetected():
    rr = run_task(None)
    assert rr.context == EXPECTED_CONTEXT and rr.final == EXPECTED_FINAL
    assert rr.completed and rr.steps_used == M_STEPS
    assert is_correct(rr)
    assert not loop_detect(rr).fired
    assert not context_integrity_detect(rr).fired


def test_context_drift_is_coherent_but_wrong():
    rr = run_task("context_drift")
    assert rr.completed and rr.steps_used == M_STEPS       # terminates fine
    assert rr.final == sum(rr.context)                      # internally consistent
    assert not is_correct(rr)                               # but wrong vs oracle
    assert context_integrity_detect(rr).fired is False      # consistency MISSES it


def test_context_inconsistent_breaks_the_invariant():
    rr = run_task("context_inconsistent")
    assert rr.final != sum(rr.context)
    assert context_integrity_detect(rr).fired is True       # consistency CATCHES it
    assert not is_correct(rr)


def test_repetition_is_deterministically_detected():
    rr = run_task("repetition")
    assert not rr.completed
    assert repetition_detect(rr).fired is True
    assert loop_detect(rr).fired is True


def test_budget_exhaustion_is_deterministically_detected():
    rr = run_task("budget_exhaustion")
    assert rr.steps_used >= STEP_BUDGET and not rr.completed
    assert budget_detect(rr).fired is True
    assert repetition_detect(rr).fired is False             # no repeated step here
    assert loop_detect(rr).fired is True


def test_task_is_deterministic():
    assert run_task("context_drift").to_dict() == run_task("context_drift").to_dict()
