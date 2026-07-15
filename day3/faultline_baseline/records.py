"""Typed records and the frozen configuration for the baseline.

Reproducibility rule (this is the Day-3 fail condition): the entire baseline is a
pure function of `BaselineConfig`. Every constant that could move a number — the
master seed, the tier definitions, the price, the latency model, the Wilson z —
lives here and is serialized into baseline.json. Given the committed config, the
committed baseline must regenerate byte-for-byte.
"""
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

_STRICT = ConfigDict(extra="forbid")
_FROZEN = ConfigDict(extra="forbid", frozen=True)

SPEC_VERSION = "3.0.0"


class Tier(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class RunStatus(str, Enum):
    SOLVED = "solved"
    INCOMPLETE = "incomplete"
    INVALID = "invalid"


# ---- configuration (the reproducibility contract) --------------------------
class CostModel(BaseModel):
    model_config = _FROZEN
    chars_per_token: int = Field(4, gt=0)
    base_prompt_chars: int = Field(200, ge=0)   # per-task prompt overhead
    price_per_1k_tokens_usd: float = Field(0.5, ge=0)


class LatencyModel(BaseModel):
    model_config = _FROZEN
    tool_base_ms: Dict[str, float] = Field(
        default_factory=lambda: {"search": 5.0, "lookup": 3.0, "calc": 1.0}
    )
    per_token_ms: float = Field(0.05, ge=0)


class TierSpec(BaseModel):
    model_config = _FROZEN
    tier: Tier
    hops: List[int] = Field(min_length=1)   # hop counts this tier samples from


class BaselineConfig(BaseModel):
    model_config = _FROZEN
    spec_version: str = SPEC_VERSION
    master_seed: int = 20260714
    n_per_tier: int = 500
    step_cap: int = 12
    wilson_z: float = 1.96                  # 95% confidence
    cost: CostModel = Field(default_factory=CostModel)
    latency: LatencyModel = Field(default_factory=LatencyModel)
    tiers: List[TierSpec] = Field(
        default_factory=lambda: [
            TierSpec(tier=Tier.EASY, hops=[1, 2, 3]),
            TierSpec(tier=Tier.MEDIUM, hops=[4, 5, 6]),   # straddles the budget cliff
            TierSpec(tier=Tier.HARD, hops=[6, 7, 8]),
        ]
    )


# ---- per-run result record -------------------------------------------------
class RunRecord(BaseModel):
    model_config = _STRICT
    task_id: str
    declared_tier: Tier            # the tier this task was filed under
    actual_tier: Optional[Tier]    # tier implied by its real hop count (None if unknown)
    mislabeled: bool               # declared_tier != actual_tier
    env_seed: int
    task_seed: int
    hops: int = Field(ge=0)
    step_cap: int = Field(gt=0)
    status: RunStatus
    success: bool                  # solved AND passed the semantic verdict
    steps_used: int = Field(ge=0)
    tokens_total: int = Field(ge=0)
    cost_usd: float = Field(ge=0)
    latency_ms: float = Field(ge=0)


# ---- aggregates ------------------------------------------------------------
class TierAggregate(BaseModel):
    model_config = _STRICT
    tier: Tier
    n: int = Field(ge=0)
    successes: int = Field(ge=0)
    success_rate: float
    wilson_low: float
    wilson_high: float
    steps_mean: float
    steps_median: float
    tokens_mean: float
    cost_usd_mean: float
    latency_ms_mean: float
    latency_ms_p95: float
    hop_histogram: Dict[str, int]


class HopPoint(BaseModel):
    model_config = _STRICT
    hops: int
    n: int
    successes: int
    success_rate: float
    wilson_low: float
    wilson_high: float


class Baseline(BaseModel):
    model_config = _STRICT
    spec_version: str
    config: BaselineConfig
    content_hash: str              # sha256 over (config + aggregates), the repro key
    tiers: List[TierAggregate]
    success_vs_hops: List[HopPoint]
