"""Resilient wrapper for ModelInterface with circuit breaker, timeout, and bounded retries."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from faultline_p2.agent.model import ModelInterface, ModelResponse
from .breaker import CircuitBreaker, CircuitBreakerOpenError, BreakerState
from .retry import RetryPolicy


class ResilientModel(ModelInterface):
    """Wraps any ModelInterface with a circuit breaker, per-call timeout, and bounded retries."""

    def __init__(
        self,
        inner_model: ModelInterface,
        retry_policy: Optional[RetryPolicy] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        timeout_seconds: Optional[float] = None,
    ) -> None:
        self.inner_model = inner_model
        self.retry_policy = retry_policy or RetryPolicy()
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.timeout_seconds = timeout_seconds

        # Model attributes forwarded from inner model
        self.model_name = getattr(inner_model, "model_name", "resilient_model")
        self.provider = getattr(inner_model, "provider", "local")
        self.version = getattr(inner_model, "version", "1.0")

        # Telemetry
        self.total_invocations: int = 0
        self.total_attempts: int = 0
        self.retried_calls: int = 0
        self.fast_fails: int = 0
        self.successful_calls: int = 0

    def generate(self, messages: List[Dict[str, Any]]) -> ModelResponse:
        self.total_invocations += 1

        last_exception: Optional[Exception] = None
        max_attempts = self.retry_policy.max_retries + 1

        for attempt in range(max_attempts):
            # Check circuit breaker before each attempt
            if not self.circuit_breaker.allow_request():
                self.fast_fails += 1
                raise CircuitBreakerOpenError("Circuit breaker is OPEN; request rejected without network call")

            self.total_attempts += 1
            if attempt > 0:
                self.retried_calls += 1

            t_start = time.time()
            try:
                # Per-call timeout simulation/enforcement
                response = self.inner_model.generate(messages)
                elapsed = time.time() - t_start
                if self.timeout_seconds and elapsed > self.timeout_seconds:
                    raise TimeoutError(f"Call duration {elapsed:.2f}s exceeded timeout {self.timeout_seconds}s")

                self.circuit_breaker.on_success()
                self.successful_calls += 1
                return response

            except Exception as exc:
                last_exception = exc
                if attempt < self.retry_policy.max_retries:
                    self.retry_policy.wait(attempt)
                else:
                    self.circuit_breaker.on_failure()
                    break

        if last_exception:
            raise last_exception
        raise RuntimeError("ResilientModel call exhausted with unknown error")
