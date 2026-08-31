from __future__ import annotations

from faultline_launch.audit import audit_day30
from faultline_launch.evidence import DAY30, load_json


def test_one_or_two_bounded_contribution_packets() -> None:
    audit = audit_day30()
    assert 1 <= audit["oss"]["packets"] <= 2
    assert audit["checks"]["oss_has_no_unmeasured_scope"] is True


def test_prepared_patch_is_not_counted_as_opened() -> None:
    source = load_json(DAY30 / "oss_contributions.json")
    opened = sum(
        item["status"] in {"opened", "merged"} for item in source["contributions"]
    )
    audit = audit_day30()
    assert audit["oss"]["opened_or_merged"] == opened
    assert audit["checks"]["one_or_two_oss_contributions"] is (1 <= opened <= 2)


def test_launch_plan_has_three_gated_windows() -> None:
    plan = load_json(DAY30 / "first_72_hours.json")
    assert [window["hours"] for window in plan["windows"]] == [
        "0-24",
        "24-48",
        "48-72",
    ]
    for window in plan["windows"]:
        assert window["owner"]
        assert window["exit_gate"]
        assert window["rollback"]
        assert {"correct_service_success", "mean_cost", "p95_latency"} <= set(
            window["metrics"]
        )
