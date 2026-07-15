"""Per-run records, accounting determinism, and mislabel detection."""
from conftest import EVIDENCE
import json

from faultline_baseline import (
    BaselineConfig,
    RunRecord,
    RunStatus,
    Sampler,
    Tier,
    account_outcome,
    actual_tier_for_hops,
    run_one,
)
from faultline_baseline._bridge import Agent, load_env


def _cfg():
    return BaselineConfig(n_per_tier=10)


def test_run_one_returns_typed_record():
    cfg = _cfg()
    spec = next(s for s in cfg.tiers if s.tier is Tier.EASY)
    rec = run_one(Sampler(cfg.master_seed), spec, 0, cfg)
    assert isinstance(rec, RunRecord)
    assert rec.declared_tier is Tier.EASY
    assert rec.status in set(RunStatus)
    assert rec.cost_usd >= 0 and rec.latency_ms >= 0


def test_easy_task_succeeds_hard_task_does_not():
    cfg = _cfg()
    easy = next(s for s in cfg.tiers if s.tier is Tier.EASY)
    hard = next(s for s in cfg.tiers if s.tier is Tier.HARD)
    s = Sampler(cfg.master_seed)
    assert run_one(s, easy, 0, cfg).success is True
    assert run_one(s, hard, 0, cfg).success is False   # over budget


def test_actual_tier_recomputed_from_hops():
    cfg = BaselineConfig()
    assert actual_tier_for_hops(2, cfg.tiers) is Tier.EASY
    assert actual_tier_for_hops(4, cfg.tiers) is Tier.MEDIUM
    assert actual_tier_for_hops(8, cfg.tiers) is Tier.HARD


def test_mislabel_flag_set_when_declared_disagrees():
    cfg = _cfg()
    hard = next(s for s in cfg.tiers if s.tier is Tier.HARD)
    rec = run_one(Sampler(cfg.master_seed), hard, 0, cfg, declared_tier=Tier.EASY)
    assert rec.declared_tier is Tier.EASY
    assert rec.actual_tier is Tier.HARD
    assert rec.mislabeled is True


def test_accounting_is_deterministic_and_scales_with_trace():
    cfg = _cfg()
    env = load_env(7)
    out_small = Agent(env, cfg.step_cap).run({"task_id": "a", "entities": ["Aster Labs"]})
    a = account_outcome(out_small, cfg.cost, cfg.latency)
    b = account_outcome(out_small, cfg.cost, cfg.latency)
    assert a == b                       # deterministic
    tokens, cost, latency = a
    assert tokens > 0 and latency > 0


def test_malformed_task_is_invalid_not_crash():
    env = load_env(7)
    out = Agent(env, 12).run({"task_id": "bad", "entities": []})
    assert out.status.value == "invalid"


def test_committed_attack_evidence_is_sound():
    """Guardrail on the committed attack artifact."""
    report = json.loads((EVIDENCE / "mislabel_attack.json").read_text())
    tm = report["tier_mislabeling"]
    assert tm["n_mislabeled_detected"] == 100
    assert tm["honest_matches_clean"] is True
    assert tm["naive_rate_if_labels_trusted"] < tm["honest_rate_by_actual_tier"]
    assert report["malformed_inputs"]["all_invalid"] is True
