from faultline_p2.env.corpus import build_corpus
corpus = build_corpus()
for sc in corpus.scenarios:
    if sc.tier == "T2":
        print(sc.prompt)
        break
