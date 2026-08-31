from __future__ import annotations

from faultline_launch.evidence import DAY30, load_json
from faultline_launch.outreach import build_outreach_report


def test_exactly_eight_tailored_messages() -> None:
    report = build_outreach_report()
    assert report["target_count"] == 8
    assert report["message_count"] == 8
    assert report["all_tailored"] is True
    assert all(item["passed"] for item in report["audits"])


def test_each_message_has_verified_result_and_limitation() -> None:
    report = build_outreach_report()
    for item in report["audits"]:
        assert item["checks"]["evidence_number_verified"] is True
        assert item["checks"]["limitation_present"] is True
        assert item["checks"]["specific_ask_present"] is True


def test_drafts_are_not_counted_as_sent() -> None:
    source = load_json(DAY30 / "outreach_targets.json")
    report = build_outreach_report()
    expected = sum(target["status"] == "sent" for target in source["targets"])
    assert report["sent_count"] == expected
    assert report["external_delivery_complete"] is (
        expected >= source["minimum_selective_sends"]
    )
