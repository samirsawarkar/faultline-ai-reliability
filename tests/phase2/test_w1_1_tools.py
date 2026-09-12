import pytest
from faultline_p2.agent.contracts import SearchCall, LookupCall, TOOL_CALL_ADAPTER
from faultline_p2.agent.tools import ToolBox

def test_retrieval_cannot_match_on_id():
    env = {
        "documents": [
            {"id": "doc-0001", "title": "Fact Document doc-0001", "text": "Some text."},
            {"id": "link-1a2b3c4d5e6f", "title": "Affiliation record link-1a2b3c4d5e6f", "text": "Affiliation text"}
        ]
    }
    tb = ToolBox(env)
    
    # Searching by ID should return nothing
    res = tb.search(SearchCall(query="doc-0001"))
    assert res.ok
    assert len(res.candidates) == 0
    
    res2 = tb.search(SearchCall(query="link-1a2b3c4d5e6f"))
    assert res2.ok
    assert len(res2.candidates) == 0

def test_lookup_refuses_unsurfaced_id():
    env = {
        "documents": [
            {"id": "doc-0001", "title": "Fact", "text": "Text"},
            {"id": "link-1a2b3c4d5e6f", "title": "Link", "text": "Text"}
        ]
    }
    tb = ToolBox(env)
    
    # Not surfaced yet
    call1 = TOOL_CALL_ADAPTER.validate_python({"tool": "lookup", "doc_id": "doc-0001"})
    res1 = tb.dispatch(call1)
    assert not res1.ok
    assert "not been surfaced" in res1.error
    
    # Search surfaces it
    tb.search(SearchCall(query="Fact"))
    res2 = tb.dispatch(call1)
    assert res2.ok
    assert res2.title == "Fact"

def test_search_snippet():
    env = {
        "documents": [
            {"id": "doc-0001", "title": "Fact", "text": "A very long text that contains the answer somewhere inside it."}
        ]
    }
    tb = ToolBox(env)
    res = tb.search(SearchCall(query="answer somewhere"))
    assert res.ok
    assert len(res.candidates) == 1
    assert "answer somewhere" in res.candidates[0].snippet
