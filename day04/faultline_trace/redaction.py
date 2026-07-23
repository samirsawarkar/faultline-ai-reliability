"""Redaction policy — what a span is allowed to remember.

Two leaks a tracer classically causes:
  1. Storing raw payloads (prompts, tool args, results) that contain secrets.
  2. Storing raw exception messages that interpolate secrets
     (e.g. RuntimeError(f"auth failed for token={token}")).

Policy:
  * Payloads are reduced to a PayloadRef (sha256 + size + bounded preview),
    all computed from the REDACTED canonical form. Nothing sensitive survives.
  * Sensitive dict keys are replaced wholesale; sensitive substrings inside any
    string (including error messages) are masked by pattern.

This module is pure and deterministic: same input -> same PayloadRef/message.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .schema import PayloadRef, SpanError

# Keys whose values are dropped entirely, at any depth.
SENSITIVE_KEYS = frozenset({
    "secret", "password", "passwd", "token", "api_key", "apikey",
    "authorization", "auth", "answer",
})

# Substring patterns masked anywhere they appear in a string, including inside
# exception messages. Order-independent; applied case-insensitively.
_SENSITIVE_PATTERNS = [
    re.compile(r"(?i)\b(secret|password|passwd|token|api_key|apikey|auth)\s*=\s*\S+"),
    re.compile(r"(?i)\bBearer\s+\S+"),
]

REDACTED = "***REDACTED***"
PREVIEW_LIMIT = 120  # chars of redacted canonical form kept as a preview


def _mask_string(s: str) -> str:
    for pat in _SENSITIVE_PATTERNS:
        s = pat.sub(lambda m: m.group(0).split("=")[0] + "=" + REDACTED
                    if "=" in m.group(0) else REDACTED, s)
    return s


def redact(obj: Any) -> Any:
    """Return a redacted deep copy: sensitive keys dropped, secrets in strings
    masked. Non-JSON types are stringified (and then masked)."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if str(k).lower() in SENSITIVE_KEYS:
                out[str(k)] = REDACTED
            else:
                out[str(k)] = redact(v)
        return out
    if isinstance(obj, (list, tuple)):
        return [redact(v) for v in obj]
    if isinstance(obj, str):
        return _mask_string(obj)
    if isinstance(obj, (int, float, bool)) or obj is None:
        return obj
    return _mask_string(repr(obj))


def _canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=True,
                      separators=(",", ":")).encode("utf-8")


def reference(payload: Any) -> PayloadRef:
    """Reduce a payload to a leak-free, content-addressed reference."""
    red = redact(payload)
    canon = _canonical(red)
    preview = canon.decode("ascii")
    truncated = len(preview) > PREVIEW_LIMIT
    if truncated:
        preview = preview[:PREVIEW_LIMIT] + "...(truncated)"
    return PayloadRef(
        sha256=hashlib.sha256(canon).hexdigest(),
        size_bytes=len(canon),
        preview=preview,
        redacted=(red != payload),
    )


def error_of(exc: BaseException) -> SpanError:
    """Capture an exception as a redacted SpanError. The message is masked so a
    secret interpolated into the exception text never reaches the trace."""
    return SpanError(type=type(exc).__name__, message=_mask_string(str(exc)))
