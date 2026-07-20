"""The three tools are typed, deterministic, and calc is not an eval hole."""
from _agent_testkit import entities

from faultline_agent import (
    CalcCall,
    CalcResult,
    LookupCall,
    LookupResult,
    SearchCall,
    SearchResult,
    ToolBox,
    load_env,
)


def _box(seed=7):
    return ToolBox(load_env(seed))


def test_search_ranks_fact_doc_above_distractor():
    env = load_env(7)
    name = entities(env, 1)[0]
    res = _box().search(SearchCall(query=name))
    assert isinstance(res, SearchResult) and res.ok
    # exact-title fact doc must rank first (score 3.0) over memos that merely
    # mention the entity in body text.
    assert res.candidates[0].title == name
    assert res.candidates[0].score == 3.0


def test_search_is_deterministic():
    a = _box().search(SearchCall(query="labs"))
    b = _box().search(SearchCall(query="labs"))
    assert a.model_dump() == b.model_dump()


def test_lookup_unknown_doc_is_structured_error():
    res = _box().lookup(LookupCall(doc_id="doc-9999"))
    assert isinstance(res, LookupResult)
    assert res.ok is False and res.error and res.text is None


def test_calc_does_basic_integer_arithmetic():
    res = _box().calc(CalcCall(expression="4000 + 4001 + -1"))
    assert isinstance(res, CalcResult) and res.ok
    assert res.value == 8000


def test_calc_refuses_names_and_calls():
    for expr in ["__import__('os').system('ls')", "open('x')", "a+1", "2**64", "1/0"]:
        res = _box().calc(CalcCall(expression=expr))
        assert res.ok is False, f"calc must refuse: {expr!r}"
        assert res.value is None


def test_calc_rejects_oversized_result():
    res = _box().calc(CalcCall(expression="999999 * 999999 * 999999"))
    assert res.ok is False and "magnitude" in (res.error or "")
