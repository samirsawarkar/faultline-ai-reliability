"""Unit tests for resilience module: circuit breaker, retry policy, fault injection, and contrast."""
import time
import pytest
from faultline_p2.resilience.breaker import CircuitBreaker, BreakerState, CircuitBreakerOpenError
from faultline_p2.resilience.retry import RetryPolicy
from faultline_p2.resilience.fault_endpoint import FaultInjectingEndpoint
from faultline_p2.resilience.resilient_model import ResilientModel
from faultline_p2.agent.model import StubModel, ModelResponse
from faultline_p2.agent.contracts import ScenarioTask, OutcomeStatus
from faultline_p2.agent.agent import run_agent
from faultline_p2.env.corpus import build_corpus
from faultline_p2.stats.intervals import wilson_interval


def test_circuit_breaker_transitions_and_cooldown():
    """Verify CLOSED -> OPEN -> HALF_OPEN -> CLOSED state lifecycle."""
    current_time = 1000.0
    def mock_time():
        return current_time

    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=5.0, time_fn=mock_time)
    assert breaker.state == BreakerState.CLOSED
    assert breaker.allow_request() is True

    # 2 failures do not trip
    breaker.on_failure()
    breaker.on_failure()
    assert breaker.state == BreakerState.CLOSED

    # 3rd failure trips to OPEN
    breaker.on_failure()
    assert breaker.state == BreakerState.OPEN

    # Requests while OPEN are rejected (fast fail)
    assert breaker.allow_request() is False
    assert breaker.fast_fails == 1

    # Fast forward time past cooldown (5s)
    current_time += 6.0

    # Probe request permitted, state transitions to HALF_OPEN
    assert breaker.allow_request() is True
    assert breaker.state == BreakerState.HALF_OPEN

    # Successful probe restores breaker to CLOSED
    breaker.on_success()
    assert breaker.state == BreakerState.CLOSED
    assert breaker.failure_count == 0


def test_circuit_breaker_half_open_failure_trips_back_to_open():
    """Verify failed probe in HALF_OPEN trips immediately back to OPEN."""
    current_time = 100.0
    breaker = CircuitBreaker(failure_threshold=2, cooldown_seconds=10.0, time_fn=lambda: current_time)

    breaker.on_failure()
    breaker.on_failure()
    assert breaker.state == BreakerState.OPEN

    # Advance past cooldown
    current_time += 11.0
    assert breaker.allow_request() is True
    assert breaker.state == BreakerState.HALF_OPEN

    # Probe fails
    breaker.on_failure()
    assert breaker.state == BreakerState.OPEN
    assert breaker.allow_request() is False


def test_retry_policy_deterministic_jitter():
    """Verify seeded backoff and jitter is 100% deterministic."""
    p1 = RetryPolicy(max_retries=3, initial_backoff_s=0.1, seed=42, sleep_fn=lambda _: None)
    p2 = RetryPolicy(max_retries=3, initial_backoff_s=0.1, seed=42, sleep_fn=lambda _: None)

    backoffs_1 = [p1.compute_backoff(i) for i in range(4)]
    backoffs_2 = [p2.compute_backoff(i) for i in range(4)]

    assert backoffs_1 == backoffs_2
    assert len(backoffs_1) == 4
    for b in backoffs_1:
        assert b > 0.0


def test_circuit_breaker_drops_downstream_calls_under_sustained_failure():
    """C4: Under sustained failure, endpoint calls drop due to fast-fails, and recovers when restored."""
    mock_clock = [0.0]
    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=10.0, time_fn=lambda: mock_clock[0])
    retry = RetryPolicy(max_retries=0, sleep_fn=lambda _: None)

    # Injected endpoint that always fails with 5xx
    failing_endpoint = FaultInjectingEndpoint(failure_rate=1.0, error_types=["5xx"])
    resilient_model = ResilientModel(failing_endpoint, retry_policy=retry, circuit_breaker=breaker)

    # Send 10 calls: first 3 reach endpoint, remaining 7 are fast-failed by breaker
    rejected_count = 0
    valid_msgs = [{"role": "system", "content": "sys"}, {"role": "user", "content": "What is the internal codename of Alpha Corp?"}]
    for _ in range(10):
        try:
            resilient_model.generate(valid_msgs)
        except CircuitBreakerOpenError:
            rejected_count += 1
        except Exception:
            pass

    # Breaker tripped after 3 failures: endpoint received only 3 calls, 7 were dropped!
    assert failing_endpoint.calls_received == 3
    assert rejected_count == 7
    assert breaker.state == BreakerState.OPEN

    # Now restore endpoint to healthy
    failing_endpoint.failure_rate = 0.0
    mock_clock[0] += 15.0  # Elapse cooldown

    # Next call probe succeeds in HALF_OPEN and closes breaker
    resp = resilient_model.generate(valid_msgs)
    assert breaker.state == BreakerState.CLOSED
    assert failing_endpoint.calls_received == 4


def test_resilience_contrast_on_agent_tasks():
    """C3: Assert task success rate with resilience beats without resilience under fault injection."""
    corpus = build_corpus()
    std_scenarios = [s for s in corpus.scenarios if s.pool == "standard"][:30]
    tasks = [ScenarioTask(task_id=s.scenario_id, prompt=s.prompt, tier=s.tier) for s in std_scenarios]
    env = {"documents": corpus.documents}

    # Arm 1: WITHOUT resilience (raw endpoint fails on transient errors)
    endpoint_unresilient = FaultInjectingEndpoint(failure_rate=0.30, seed=42)
    base_passed = sum(
        1 for t in tasks
        if run_agent(t, env, endpoint_unresilient, step_cap=12).status == OutcomeStatus.ANSWERED
    )
    base_ci = wilson_interval(base_passed, len(tasks))

    # Arm 2: WITH resilience (bounded retries + backoff + breaker recovers transient errors)
    endpoint_resilient = FaultInjectingEndpoint(failure_rate=0.30, seed=42)
    resilient_wrapper = ResilientModel(
        endpoint_resilient,
        retry_policy=RetryPolicy(max_retries=3, initial_backoff_s=0.001, seed=42, sleep_fn=lambda _: None),
        circuit_breaker=CircuitBreaker(failure_threshold=5, cooldown_seconds=0.1),
    )
    res_passed = sum(
        1 for t in tasks
        if run_agent(t, env, resilient_wrapper, step_cap=12).status == OutcomeStatus.ANSWERED
    )
    res_ci = wilson_interval(res_passed, len(tasks))

    # Assert rates, disjoint Wilson intervals (resilient lower bound > baseline upper bound)
    assert res_passed > base_passed
    assert res_ci[0] > base_ci[1], f"Expected disjoint intervals, got res={res_ci}, base={base_ci}"
    assert resilient_wrapper.retried_calls > 0  # Proves retries did the work
