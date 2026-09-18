from __future__ import annotations

from typing import Any, Dict, List, Optional

from faultline_p2.agent.contracts import Candidate, SearchResult
from faultline_p2.agent.tools import ToolBox


class OracleToolBox(ToolBox):
    """Oracle retrieval toolbox that ignores queries and returns scenario traversal_sources."""

    def __init__(
        self,
        env: Dict[str, Any],
        traversal_sources: List[str],
        max_candidates: int = 5,
    ) -> None:
        super().__init__(env, max_candidates=max_candidates)
        self.traversal_sources = list(traversal_sources)

    def search(self, call: Optional[Any] = None) -> SearchResult:
        candidates: List[Candidate] = []
        for doc_id in self.traversal_sources:
            d = self._by_id.get(doc_id)
            title = d["title"] if d else ""
            text = d["text"] if d else ""
            snippet = text[:500]
            self.surfaced_ids.add(doc_id)
            candidates.append(
                Candidate(
                    doc_id=doc_id,
                    title=title,
                    score=3.0,
                    snippet=snippet,
                )
            )
        return SearchResult(ok=True, candidates=candidates)
