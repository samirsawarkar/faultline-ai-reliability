import pytest
from faultline_p2.env.corpus import build_corpus

def test_unambiguous_links():
    corpus = build_corpus()
    link_counts = {}
    for d in corpus.documents:
        if d["id"].startswith("link-"):
            # "Affiliation record: The organization holding internal codename Zinc-4174 is officially affiliated with Dovetail Collective."
            # The "key" is everything before "is officially affiliated with"
            prefix = d["text"].split("is officially affiliated with")[0].strip()
            link_counts[prefix] = link_counts.get(prefix, 0) + 1

    ambiguous = {k: v for k, v in link_counts.items() if v > 1}
    assert not ambiguous, f"Found {len(ambiguous)} ambiguous link keys: {list(ambiguous.keys())[:5]}..."
