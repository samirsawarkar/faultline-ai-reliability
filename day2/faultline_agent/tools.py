"""The three tools the agent is allowed to use: search, lookup, calc.

Design rules (all defensive, all deterministic):
  * Every tool takes a validated *Call model and returns a validated *Result
    model. There is no raw-dict path in or out.
  * No tool uses randomness, wall-clock time, or network. Given the same env and
    the same call, a tool returns byte-identical output. That determinism is
    what makes an injected fault (Day 3+) the ONLY moving part.
  * `calc` is NOT `eval`. It walks a whitelisted AST (integers and + - * only).
    Anything else — names, calls, attributes, division, huge literals — is
    refused with ok=False, never executed.
"""
from __future__ import annotations

import ast
from typing import Any, Dict, List

from .contracts import (
    CalcCall,
    CalcResult,
    Candidate,
    LookupCall,
    LookupResult,
    SearchCall,
    SearchResult,
)

# Guard against absurd intermediate integers from something like 9**9**9 — but
# we do not even allow '**', so this is a belt-and-suspenders cap on results.
_MAX_ABS_VALUE = 10 ** 12


def _norm(s: str) -> str:
    return " ".join(str(s).strip().lower().split())


class ToolBox:
    """Tools bound to one immutable environment (a Day-1 build_env dict)."""

    def __init__(self, env: Dict[str, Any], max_candidates: int = 5) -> None:
        self._docs: List[Dict[str, Any]] = list(env["documents"])
        self._by_id: Dict[str, Dict[str, Any]] = {d["id"]: d for d in self._docs}
        self._max_candidates = max_candidates

    # -- search ------------------------------------------------------------
    def search(self, call: SearchCall) -> SearchResult:
        """Rank documents by how well `query` matches. Deterministic order.

        Scoring, highest first:
          3.0  query equals the (normalized) title exactly
          2.0  query is a substring of the title
          1.0  query is a substring of the body text only
        Ties break by doc_id ascending, so the ordering never depends on dict
        or hash iteration order.
        """
        q = _norm(call.query)
        scored: List[Candidate] = []
        for d in self._docs:
            title_n = _norm(d["title"])
            text_n = _norm(d["text"])
            if q == title_n:
                score = 3.0
            elif q in title_n:
                score = 2.0
            elif q in text_n:
                score = 1.0
            else:
                continue
            scored.append(Candidate(doc_id=d["id"], title=d["title"], score=score))
        scored.sort(key=lambda c: (-c.score, c.doc_id))
        return SearchResult(ok=True, candidates=scored[: self._max_candidates])

    # -- lookup ------------------------------------------------------------
    def lookup(self, call: LookupCall) -> LookupResult:
        d = self._by_id.get(call.doc_id)
        if d is None:
            return LookupResult(ok=False, error=f"unknown doc_id: {call.doc_id}")
        return LookupResult(ok=True, doc_id=d["id"], title=d["title"], text=d["text"])

    # -- calc --------------------------------------------------------------
    def calc(self, call: CalcCall) -> CalcResult:
        try:
            value = _safe_arith(call.expression)
        except _CalcError as e:
            return CalcResult(ok=False, expression=call.expression, error=str(e))
        return CalcResult(ok=True, expression=call.expression, value=value)

    # -- single validated dispatch entry point -----------------------------
    def dispatch(self, call: Any) -> Any:
        """Route a validated ToolCall to its handler. Exhaustive by type."""
        if isinstance(call, SearchCall):
            return self.search(call)
        if isinstance(call, LookupCall):
            return self.lookup(call)
        if isinstance(call, CalcCall):
            return self.calc(call)
        raise TypeError(f"not a validated ToolCall: {type(call).__name__}")


# --- safe arithmetic --------------------------------------------------------
class _CalcError(ValueError):
    pass


# Only these AST node types may appear. Note the absence of Call, Name,
# Attribute, Subscript, Pow, Div — the classic eval-injection surfaces.
_ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult)
_ALLOWED_UNARY = (ast.UAdd, ast.USub)


def _safe_arith(expr: str) -> int:
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise _CalcError(f"not a valid arithmetic expression: {e.msg}")
    value = _eval_node(tree.body)
    if abs(value) > _MAX_ABS_VALUE:
        raise _CalcError("result exceeds the allowed magnitude")
    return value


def _eval_node(node: ast.AST) -> int:
    if isinstance(node, ast.BinOp) and isinstance(node.op, _ALLOWED_BINOPS):
        left, right = _eval_node(node.left), _eval_node(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        return left * right
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, _ALLOWED_UNARY):
        operand = _eval_node(node.operand)
        return +operand if isinstance(node.op, ast.UAdd) else -operand
    # Python 3.8+: integer literals arrive as ast.Constant.
    if isinstance(node, ast.Constant):
        if isinstance(node.value, int) and not isinstance(node.value, bool):
            return node.value
        raise _CalcError("only integer literals are allowed")
    raise _CalcError(f"disallowed expression element: {type(node).__name__}")
