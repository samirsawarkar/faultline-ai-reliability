from faultline_p2.env.corpus import build_corpus
corpus = build_corpus()
prompts = set()
for sc in corpus.scenarios:
    prompts.add(sc.prompt.split("?")[0] + "?")
for p in prompts:
    print(p)
