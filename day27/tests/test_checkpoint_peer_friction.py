from faultline_cold_repro import (
    audit_friction,
    audit_peer,
    build_report,
    render_checkpoint,
)


def test_every_friction_defect_is_resolved_and_verified():
    audit = audit_friction()
    assert audit["passed"]
    assert len(audit["report"]["entries"]) == 11


def test_independent_peer_attempt_is_requested_and_honestly_recorded():
    audit = audit_peer()
    assert audit["passed"]
    assert audit["report"]["cold_context"]
    assert audit["report"]["operator_improvisations"] == 0
    assert (
        audit["report"]["execution"]["status"]
        == "blocked_external_approval"
    )


def test_checkpoint_27_passes_all_positive_gates():
    report = build_report(require_peer=True)
    checkpoint = report["checkpoint_27"]
    assert checkpoint["passed"]
    assert not checkpoint["fail_condition_triggered"]
    assert checkpoint["checks"]["no_undocumented_local_knowledge_required"]


def test_checkpoint_renderer_is_explicit_about_the_fail_condition():
    rendered = render_checkpoint(build_report(require_peer=True))
    assert "no_undocumented_local_knowledge_required | True" in rendered
    assert "Fail condition triggered: **False**" in rendered
    assert "Checkpoint passed: **True**" in rendered
