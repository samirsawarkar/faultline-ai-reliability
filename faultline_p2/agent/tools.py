import ast
from typing import Any, Dict, List, Set

from .contracts import (
    CalcCall,
    CalcResult,
    Candidate,
    LookupCall,
    LookupResult,
    SearchCall,
    SearchResult,
)

_MAX_ABS_VALUE = 10 ** 12

def _norm(s: str) -> str:
    return " ".join(str(s).strip().lower().split())

class ToolBox:
    def __init__(self, env: Dict[str, Any], max_candidates: int = 5) -> None:
        self._docs: List[Dict[str, Any]] = list(env["documents"])
        self._by_id: Dict[str, Dict[str, Any]] = {d["id"]: d for d in self._docs}
        self._max_candidates = max_candidates
        self.surfaced_ids: Set[str] = set()

    def search(self, call: SearchCall) -> SearchResult:
        q = _norm(call.query)
        scored: List[Candidate] = []
        for d in self._docs:
            title_n = _norm(d["title"].replace(d["id"], ""))
            text_n = _norm(d["text"].replace(d["id"], ""))
            
            score = 0.0
            snippet = ""
            if q == title_n:
                score = 3.0
                snippet = d["text"][:500]
            elif q in title_n:
                score = 2.0
                snippet = d["text"][:500]
            elif q in text_n:
                score = 1.0
                # find index of match in original text (approximate by finding in lowered)
                idx = d["text"].lower().find(q.lower())
                if idx == -1: idx = 0
                start = max(0, idx - 250)
                end = min(len(d["text"]), start + 500)
                snippet = d["text"][start:end]
            else:
                continue
                
            self.surfaced_ids.add(d["id"])
            scored.append(Candidate(doc_id=d["id"], title=d["title"], score=score, snippet=snippet))
            
        scored.sort(key=lambda c: (-c.score, c.doc_id))
        return SearchResult(ok=True, candidates=scored[: self._max_candidates])

    def lookup(self, call: LookupCall) -> LookupResult:
        if call.doc_id not in self.surfaced_ids:
            return LookupResult(ok=False, error=f"ID {call.doc_id} has not been surfaced by search in this run")
            
        d = self._by_id.get(call.doc_id)
        if d is None:
            return LookupResult(ok=False, error=f"unknown doc_id: {call.doc_id}")
        return LookupResult(ok=True, doc_id=d["id"], title=d["title"], text=d["text"])

    def calc(self, call: CalcCall) -> CalcResult:
        try:
            value = _safe_arith(call.expression)
        except _CalcError as e:
            return CalcResult(ok=False, expression=call.expression, error=str(e))
        return CalcResult(ok=True, expression=call.expression, value=value)

    def dispatch(self, call: Any) -> Any:
        if isinstance(call, SearchCall):
            return self.search(call)
        if isinstance(call, LookupCall):
            return self.lookup(call)
        if isinstance(call, CalcCall):
            return self.calc(call)
        raise TypeError(f"not a validated ToolCall: {type(call).__name__}")

class _CalcError(ValueError):
    pass

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
        if isinstance(node.op, ast.Add): return left + right
        if isinstance(node.op, ast.Sub): return left - right
        return left * right
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, _ALLOWED_UNARY):
        operand = _eval_node(node.operand)
        return +operand if isinstance(node.op, ast.UAdd) else -operand
    if isinstance(node, ast.Constant):
        if isinstance(node.value, int) and not isinstance(node.value, bool):
            return node.value
        raise _CalcError("only integer literals are allowed")
    raise _CalcError(f"disallowed expression element: {type(node).__name__}")
