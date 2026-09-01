from faultline_p2.env.corpus import build_corpus
corpus = build_corpus()
link_counts = {}
for d in corpus.documents:
    if d["id"].startswith("link-"):
        prefix = d["text"].split("is officially affiliated with")[0]
        link_counts[prefix] = link_counts.get(prefix, 0) + 1

print(sum(1 for v in link_counts.values() if v > 1), "ambiguous prefixes")
