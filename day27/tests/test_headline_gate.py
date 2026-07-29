import json
from pathlib import Path

from faultline_cold_repro import (
    build_headline_result,
    render_headline_result,
)

ROOT = Path(__file__).resolve().parents[2]


def test_saved_headlines_resolve_without_running_generators():
    report = build_headline_result(run_generators=False)
    assert report["passed"]
    assert len(report["headlines"]) == 6


def test_headline_renderer_matches_the_documented_terminal_block():
    report = build_headline_result(run_generators=False)
    rendered = render_headline_result(report)
    assert "headline tool_hops: Measured success 0.818" in rendered
    assert "headline tests: 433 tests collected and passed" in rendered
    assert rendered.endswith("cold reproduction: PASS")


def test_each_headline_has_matching_typed_values():
    report = build_headline_result(run_generators=False)
    assert all(item["values_match"] for item in report["headlines"])
    assert report["test_gate"] == {
        "collected": 433,
        "passed": 433,
        "passed_all": True,
    }


def test_registered_generator_commands_are_explicit_make_targets():
    manifest = json.loads(
        (ROOT / "day26/readme_claims.json").read_text(encoding="utf-8")
    )
    commands = [claim["command"] for claim in manifest["claims"]]
    assert len(commands) == len(set(commands))
    assert all(command.startswith("make ") for command in commands)
    assert all(
        not any(token in command for token in (";", "&&", "||", "$("))
        for command in commands
    )
    source = (
        ROOT / "day27/faultline_cold_repro/headlines.py"
    ).read_text(encoding="utf-8")
    assert 'f"PY={sys.executable}"' in source
