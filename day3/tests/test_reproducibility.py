"""The Day-3 gate: the baseline must reproduce from committed seeds + config.

If any of these fail, the mission fails by definition.
"""
import json
from pathlib import Path

EVIDENCE = Path(__file__).resolve().parents[1] / "evidence"

from faultline_baseline import (
    BaselineConfig,
    build_baseline,
    render_success_vs_hops,
    task_seed,
)
from faultline_baseline.records import Tier


def test_task_seed_is_pure_arithmetic():
    # Same inputs -> same seed, always; disjoint lanes per tier.
    assert task_seed(20260714, Tier.EASY, 7) == task_seed(20260714, Tier.EASY, 7)
    lanes = {task_seed(1, t, 0) for t in (Tier.EASY, Tier.MEDIUM, Tier.HARD)}
    assert len(lanes) == 3


def test_build_is_deterministic_small():
    a, _ = build_baseline(BaselineConfig(n_per_tier=50))
    b, _ = build_baseline(BaselineConfig(n_per_tier=50))
    assert a.content_hash == b.content_hash
    assert a.model_dump(mode="json") == b.model_dump(mode="json")


def test_committed_baseline_matches_fresh_build():
    """Rebuild with the default (committed) config and match the committed hash.
    This is the literal fail condition: reproduce baseline.json from config."""
    committed = json.loads((EVIDENCE / "baseline.json").read_text())
    fresh, _ = build_baseline(BaselineConfig())
    assert fresh.content_hash == committed["content_hash"]
    assert fresh.model_dump(mode="json") == committed


def test_committed_figure_matches_fresh_render():
    committed_svg = (EVIDENCE / "success_vs_hops.svg").read_text()
    fresh, _ = build_baseline(BaselineConfig())
    assert render_success_vs_hops(fresh.success_vs_hops, BaselineConfig()) == committed_svg


def test_config_is_frozen():
    cfg = BaselineConfig()
    import pydantic
    try:
        cfg.master_seed = 1  # frozen -> must raise
        raised = False
    except pydantic.ValidationError:
        raised = True
    assert raised
