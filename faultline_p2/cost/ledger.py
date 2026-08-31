"""Cost ledger, price table, budget cap enforcement, and estimation."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

_STRICT = ConfigDict(extra="forbid")

# TODO: Read caps dynamically from MEC.md once MEC is frozen
# Per-project budget caps from MEC and PHASE2-PLAN.md
DEFAULT_PROJECT_CAPS: Dict[str, float] = {
    "p00_preflight": 0.50,
    "p01_baseline": 2.00,
    "p02_otel": 0.00,
    "p03_grounding": 5.00,
    "p04_taxonomy": 0.00,
    "p05_judge": 10.00,
    "p06_passk": 45.00,
    "p07_provider": 5.00,
    "p08_mcptox": 10.00,
    "p09_redteam": 6.00,
    "p10_cascade": 8.00,
    "p11_release": 5.00,
    "p12_attribution": 6.00,
}
TOTAL_BUDGET_CEILING = 150.00


class BudgetExceeded(Exception):
    """Raised when an operation would exceed or has exceeded a project budget cap."""


class RungPricing(BaseModel):
    model_config = _STRICT
    model_name: str
    input_price_per_m: float = Field(ge=0.0)
    output_price_per_m: float = Field(ge=0.0)
    cached_input_price_per_m: Optional[float] = Field(default=None, ge=0.0)


class PriceTable(BaseModel):
    model_config = _STRICT
    rungs: Dict[str, RungPricing]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PriceTable":
        rungs = {}
        for k, v in data.items():
            rungs[k] = RungPricing(
                model_name=v.get("model_name", k),
                input_price_per_m=v["input_price_per_m"],
                output_price_per_m=v["output_price_per_m"],
                cached_input_price_per_m=v.get("cached_input_price_per_m"),
            )
        return cls(rungs=rungs)

    @classmethod
    def from_file(cls, path: Path) -> "PriceTable":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # If loaded from preflight.json
        if "rungs" in data and isinstance(data["rungs"], dict):
            return cls.from_dict(data["rungs"])
        return cls.from_dict(data)

    def get_rung(self, rung: str) -> RungPricing:
        if rung not in self.rungs:
            raise KeyError(f"Rung '{rung}' not in price table. Available: {list(self.rungs.keys())}")
        return self.rungs[rung]


class LedgerEntry(BaseModel):
    model_config = _STRICT
    run_id: str
    project: str
    rung: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    usd: float = Field(ge=0.0)
    timestamp_utc: str


def estimate(
    n_runs: int,
    in_tokens: int,
    out_tokens: int,
    rung: str,
    price_table: PriceTable,
    cached_prefix_fraction: float = 0.0,
) -> float:
    """Calculate expected cost in USD for n_runs given token sizes and pricing."""
    if n_runs < 0 or in_tokens < 0 or out_tokens < 0:
        raise ValueError("n_runs and token counts must be non-negative")
    if not (0.0 <= cached_prefix_fraction <= 1.0):
        raise ValueError("cached_prefix_fraction must be in [0.0, 1.0]")

    pricing = price_table.get_rung(rung)
    if cached_prefix_fraction > 0.0:
        if pricing.cached_input_price_per_m is None:
            raise ValueError(
                f"Cached prefix pricing not defined for rung '{rung}'. "
                f"Cannot estimate cached cost without explicit pricing."
            )
        cached_rate = pricing.cached_input_price_per_m
    else:
        cached_rate = 0.0

    uncached_in = in_tokens * (1.0 - cached_prefix_fraction)
    cached_in = in_tokens * cached_prefix_fraction

    in_cost_per_run = (uncached_in * pricing.input_price_per_m + cached_in * cached_rate) / 1_000_000.0
    out_cost_per_run = (out_tokens * pricing.output_price_per_m) / 1_000_000.0

    total = n_runs * (in_cost_per_run + out_cost_per_run)
    return round(total, 6)


class CostLedger:
    """Append-only ledger enforcing hard budget stops."""

    def __init__(
        self,
        ledger_path: Path,
        project_caps: Optional[Dict[str, float]] = None,
    ) -> None:
        self.ledger_path = Path(ledger_path)
        self.project_caps = project_caps or DEFAULT_PROJECT_CAPS

    def record(self, entry: LedgerEntry) -> None:
        """Append entry to ledger immediately."""
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(entry.model_dump(), sort_keys=True) + "\n"
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()

    def read_entries(self, project: Optional[str] = None) -> List[LedgerEntry]:
        if not self.ledger_path.exists():
            return []
        entries: List[LedgerEntry] = []
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    item = json.loads(line)
                    if project is None or item.get("project") == project:
                        entries.append(LedgerEntry(**item))
        return entries

    def spent(self, project: Optional[str] = None) -> float:
        entries = self.read_entries(project=project)
        return round(sum(e.usd for e in entries), 6)

    def check_cap(self, project: str, additional_usd: float = 0.0) -> float:
        """Check remaining cap for a project. Raises BudgetExceeded if exceeded."""
        cap = self.project_caps.get(project, 0.0)
        spent_so_far = self.spent(project=project)
        total_projected = spent_so_far + additional_usd
        if total_projected > cap:
            raise BudgetExceeded(
                f"Budget cap exceeded for project '{project}': "
                f"spent ${spent_so_far:.4f} + projected ${additional_usd:.4f} > cap ${cap:.4f}"
            )
        # Also check global ceiling
        global_spent = self.spent() + additional_usd
        if global_spent > TOTAL_BUDGET_CEILING:
            raise BudgetExceeded(
                f"Global budget ceiling exceeded: "
                f"total ${global_spent:.4f} > ceiling ${TOTAL_BUDGET_CEILING:.4f}"
            )
        return round(cap - total_projected, 6)
