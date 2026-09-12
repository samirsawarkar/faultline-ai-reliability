"""faultline_p2.env

Re-exports:
- build_env: pinned copy from day01
- build_corpus, Corpus, Scenario, HopStep: Phase 2 multi-hop corpus builder
"""
from faultline_p2.env._day01_env import build_env

__all__ = ["build_env", "build_corpus", "Corpus", "Scenario", "HopStep"]


def __getattr__(name: str):
    if name in {"build_corpus", "Corpus", "Scenario", "HopStep"}:
        import faultline_p2.env.corpus as _c
        return getattr(_c, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
