from faultline_p2.env.corpus import build_corpus
corpus = build_corpus()
for sc in corpus.scenarios:
    if sc.scenario_id == "s-0069":
        print(sc.traversal_sources)
