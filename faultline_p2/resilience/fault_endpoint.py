"""Fault-injecting fake endpoint simulating timeouts, 5xx errors, and rate limits."""
from __future__ import annotations

import random
from typing import Any, Dict, List, Optional
from faultline_p2.agent.model import ModelInterface, ModelResponse, StubModel


class FaultInjectingEndpoint(ModelInterface):
    """Simulated LLM provider endpoint with configurable failure injection."""

    def __init__(
        self,
        base_model: Optional[ModelInterface] = None,
        failure_rate: float = 0.0,
        error_types: Optional[List[str]] = None,
        burst_failures: int = 0,
        seed: int = 42,
    ) -> None:
        self.base_model = base_model or StubModel(behavior="solver")
        self.failure_rate = failure_rate
        self.error_types = error_types or ["5xx", "rate_limit", "timeout"]
        self.burst_failures_remaining = burst_failures
        self.rng = random.Random(seed)

        # Telemetry
        self.calls_received: int = 0
        self.failures_injected: int = 0
        self.successes: int = 0
        self.error_breakdown: Dict[str, int] = {"timeout": 0, "5xx": 0, "rate_limit": 0}

    def generate(self, messages: List[Dict[str, Any]]) -> ModelResponse:
        self.calls_received += 1

        # Check burst failures first
        should_fail = False
        if self.burst_failures_remaining > 0:
            should_fail = True
            self.burst_failures_remaining -= 1
        elif self.failure_rate > 0.0:
            should_fail = self.rng.random() < self.failure_rate

        if should_fail:
            self.failures_injected += 1
            err_type = self.rng.choice(self.error_types)
            self.error_breakdown[err_type] = self.error_breakdown.get(err_type, 0) + 1

            if err_type == "timeout":
                raise TimeoutError("Simulated LLM provider timeout (>2000ms)")
            elif err_type == "5xx":
                raise RuntimeError("HTTP 503 Service Unavailable: Provider overloaded")
            elif err_type == "rate_limit":
                raise RuntimeError("HTTP 429 Too Many Requests: Rate limit exceeded")
            else:
                raise RuntimeError(f"Simulated fault: {err_type}")

        self.successes += 1
        return self.base_model.generate(messages)
