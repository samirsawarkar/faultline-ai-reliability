"""FAULTLINE Day 18: bounded recovery (M1 repair-retry, M2 timeout/backoff/jitter).

Recovery that is bounded (max_attempts + budgets), safe to repeat (idempotency
ledger), and budgeted (cost + latency ceilings). Builds on Day 9 (schema), Day 14
(McNemar), Day 4 (traces).

Public surface:
    policy:      RetryPolicy, MAX_ATTEMPTS_CAP
    engine:      run_bounded_retry, RecoveryResult
    idempotency: IdempotencyLedger, NaiveNoLedger
    repair:      schema_repair_retry, make_producer (M1)
    timeout:     timeout_retry, transient_slow, persistent_slow, make_slow_tool (M2)
    experiment:  build_report, paired_m1, paired_m2, exhaustion_attack,
                 new_failure_analysis, M1_POLICY, M2_POLICY, NO_RECOVERY
"""
from . import engine, experiment, idempotency, policy, repair, timeout
from .engine import RecoveryResult, run_bounded_retry
from .experiment import (
    M1_POLICY,
    M2_POLICY,
    NO_RECOVERY,
    build_report,
    exhaustion_attack,
    new_failure_analysis,
    paired_m1,
    paired_m2,
)
from .idempotency import IdempotencyLedger, NaiveNoLedger
from .policy import MAX_ATTEMPTS_CAP, RetryPolicy
from .repair import make_producer, schema_repair_retry
from .timeout import make_slow_tool, persistent_slow, timeout_retry, transient_slow

__all__ = [
    "RetryPolicy", "MAX_ATTEMPTS_CAP",
    "run_bounded_retry", "RecoveryResult",
    "IdempotencyLedger", "NaiveNoLedger",
    "schema_repair_retry", "make_producer",
    "timeout_retry", "transient_slow", "persistent_slow", "make_slow_tool",
    "build_report", "paired_m1", "paired_m2", "exhaustion_attack",
    "new_failure_analysis", "M1_POLICY", "M2_POLICY", "NO_RECOVERY",
    "engine", "experiment", "idempotency", "policy", "repair", "timeout",
]
