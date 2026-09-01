from faultline_p2.env.corpus import build_corpus
corpus = build_corpus()
for d in corpus.documents:
    if "Cobalt-4152" in d["text"] and not d["id"].startswith("link-"):
        print(d["title"])
