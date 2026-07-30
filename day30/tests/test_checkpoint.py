from __future__ import annotations

from faultline_launch.report import build_checkpoint


def test_fail_condition_is_not_triggered() -> None:
    checkpoint = build_checkpoint()
    assert checkpoint["fail_condition_triggered"] is False
    assert checkpoint["audit"]["checks"]["recorded_mock_defense"] is True
    assert checkpoint["audit"]["checks"]["every_core_decision_defended"] is True


def test_checkpoint_pass_is_receipt_driven() -> None:
    checkpoint = build_checkpoint()
    checks = checkpoint["audit"]["checks"]
    expected = all(checks.values())
    assert checkpoint["passed"] is expected
    if not expected:
        assert checkpoint["audit"]["external_actions_pending"]
