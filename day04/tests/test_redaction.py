"""Redaction policy tests: keys dropped, secrets masked, refs leak-free."""
from __future__ import annotations

from faultline_trace import redact, reference
from faultline_trace.redaction import REDACTED, error_of


def test_sensitive_keys_dropped_at_any_depth():
    obj = {"task": "x", "secret": "s3cr3t", "nested": {"api_key": "abc", "ok": 1}}
    red = redact(obj)
    assert red["secret"] == REDACTED
    assert red["nested"]["api_key"] == REDACTED
    assert red["nested"]["ok"] == 1
    assert red["task"] == "x"


def test_secret_in_string_is_masked():
    red = redact("auth failed for token=abcdef123")
    assert "abcdef123" not in red
    assert REDACTED in red


def test_reference_is_leak_free_and_content_addressed():
    ref = reference({"prompt": "hi", "secret": "s3cr3t"})
    assert "s3cr3t" not in ref.preview
    assert ref.redacted is True
    assert len(ref.sha256) == 64
    # deterministic
    assert reference({"prompt": "hi", "secret": "s3cr3t"}).sha256 == ref.sha256


def test_preview_is_bounded():
    ref = reference({"blob": "z" * 10_000})
    assert len(ref.preview) <= 120 + len("...(truncated)")


def test_error_message_redacted():
    err = error_of(RuntimeError("boom token=xyz789"))
    assert err.type == "RuntimeError"
    assert "xyz789" not in err.message
    assert REDACTED in err.message
