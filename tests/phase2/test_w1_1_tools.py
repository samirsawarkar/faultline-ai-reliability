import pytest
from faultline_p2.agent.contracts import SearchCall, LookupCall, CalcCall, TOOL_CALL_ADAPTER
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

    # Searching by actual content should work
    res3 = tb.search(SearchCall(query="Fact Document"))
    assert res3.ok
    assert len(res3.candidates) == 1
    
    res4 = tb.search(SearchCall(query="Affiliation text"))
    assert res4.ok
    assert len(res4.candidates) == 1

def test_lookup_accepts_both_id_types():
    env = {
        "documents": [
            {"id": "doc-0001", "title": "Fact", "text": "Text"},
            {"id": "link-1a2b3c4d5e6f", "title": "Link", "text": "Text"}
        ]
    }
    tb = ToolBox(env)
    
    # Using the adapter to prove it validates
    call1 = TOOL_CALL_ADAPTER.validate_python({"tool": "lookup", "doc_id": "doc-0001"})
    res1 = tb.dispatch(call1)
    assert res1.ok
    assert res1.title == "Fact"
    
    call2 = TOOL_CALL_ADAPTER.validate_python({"tool": "lookup", "doc_id": "link-1a2b3c4d5e6f"})
    res2 = tb.dispatch(call2)
    assert res2.ok
    assert res2.title == "Link"
