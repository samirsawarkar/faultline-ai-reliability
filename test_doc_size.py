from faultline_p2.env.corpus import build_corpus
c = build_corpus()
for d in c.documents:
    if "Zephyr Systems" in d["title"]:
        print(len(d["text"]))
        print(d["text"])
