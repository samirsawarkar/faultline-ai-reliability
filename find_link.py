from faultline_p2.env.corpus import build_corpus
corpus = build_corpus()
for d in corpus.documents:
    if "Zinc-4174" in d["text"] and d["id"].startswith("link-"):
        print(d["title"])
        print(d["text"])
