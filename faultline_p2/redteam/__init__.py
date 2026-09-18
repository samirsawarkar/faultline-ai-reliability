"""FAULTLINE Redteam Module (Project P9).

Adversarial regression suite evaluating prompt injection attacks through corpus
document text across bare agents (Arm A) versus agents with RuntimePolicy (Arm B).
"""
from faultline_p2.redteam.attacks import (
    CATEGORIES,
    Attack,
    build,
    inject,
)
from faultline_p2.redteam.hostile import HostileStub
from faultline_p2.redteam.predicates import (
    SEMANTIC_ANSWER_CATEGORIES,
    STRUCTURAL_CATEGORIES,
    check_benign_correct,
    mentioned,
    succeeded,
)

__all__ = [
    "CATEGORIES",
    "SEMANTIC_ANSWER_CATEGORIES",
    "STRUCTURAL_CATEGORIES",
    "Attack",
    "build",
    "inject",
    "HostileStub",
    "mentioned",
    "succeeded",
    "check_benign_correct",
]
