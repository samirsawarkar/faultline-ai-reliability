"""The output schema and its validator — the ground the F1 detector stands on.

Day 8 injects faults and labels them; Day 9 asks a harder question: can a cheap,
deterministic detector *notice*? For structured-output corruption (F1) the
detector is a schema validator. A schema is a set of STRUCTURAL rules — types,
bounds, list shape, ordering — that a well-formed tool output must satisfy. It is
deliberately NOT an oracle: it never checks whether the answer is *correct*, only
whether it is *well-formed*. That distinction is the whole point of the Learn
block (validation catches malformed, not wrong).

The clean `DemoChannel` output for call index `i` is
    {"step": <str>, "value": (i+1)*10, "tokens": [i, i+1, i+2, i+3]}
and every rule below passes on it for i in 0..11 (value 10..120 <= 150).

`validate_output` is a pure function: same output -> same violations, forever.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

# Structural bounds. Clean values are multiples of 10 in [10, 120]; the ceiling
# leaves room so that *small* corruptions stay in-range (a plausible-but-wrong
# value the schema cannot catch) while *large* ones break out. That gap is what
# makes F1 detection severity-dependent — and honest about validation's limits.
VALUE_MIN = 10
VALUE_MAX = 150
TOKENS_LEN = 4


@dataclass(frozen=True)
class Violation:
    field: str
    code: str      # machine-stable reason code
    detail: str


def validate_output(out: Any) -> List[Violation]:
    """Return the (possibly empty) list of structural violations of `out`."""
    v: List[Violation] = []

    if not isinstance(out, dict):
        return [Violation("<root>", "not_an_object", f"expected object, got {type(out).__name__}")]

    # step: non-empty string
    step = out.get("step")
    if not isinstance(step, str) or not step:
        v.append(Violation("step", "bad_step", "step must be a non-empty string"))

    # value: int within [VALUE_MIN, VALUE_MAX]
    value = out.get("value")
    if not isinstance(value, int) or isinstance(value, bool):
        v.append(Violation("value", "value_type", "value must be an int"))
    elif not (VALUE_MIN <= value <= VALUE_MAX):
        v.append(Violation("value", "value_range",
                          f"value {value} outside [{VALUE_MIN}, {VALUE_MAX}]"))

    # tokens: list of exactly TOKENS_LEN ints, strictly consecutive (step +1)
    tokens = out.get("tokens")
    if not isinstance(tokens, list):
        v.append(Violation("tokens", "tokens_type", "tokens must be a list"))
    else:
        if len(tokens) != TOKENS_LEN:
            v.append(Violation("tokens", "tokens_length",
                              f"expected {TOKENS_LEN} tokens, got {len(tokens)}"))
        if not all(isinstance(t, int) and not isinstance(t, bool) for t in tokens):
            v.append(Violation("tokens", "tokens_item_type", "tokens must all be ints"))
        elif any(tokens[i + 1] - tokens[i] != 1 for i in range(len(tokens) - 1)):
            v.append(Violation("tokens", "tokens_not_consecutive",
                              "tokens must be strictly consecutive (+1)"))

    return v


def is_valid(out: Any) -> bool:
    return not validate_output(out)
