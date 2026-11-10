"""Researcher agent: collect sources, nothing else.

It does not summarise into claims — that separation is what lets the
critic later check claims against a stable source list.
"""
from __future__ import annotations

from ..tools.arxiv_tool import ArxivSearch
from ..tools.search_tools import FixtureSearch


class ResearcherAgent:
    name = "researcher"

    def __init__(self, fixture_search: FixtureSearch, use_online: bool = False):
        self.search = fixture_search
        self.use_online = use_online
        self.arxiv = ArxivSearch()

    def run(self, topic: str, max_sources: int = 8):
        sources = self.search.search(topic, max_results=max_sources)
        seen, deduped = set(), []
        for s in sources:
            key = s.title.lower()
            if key not in seen:
                seen.add(key)
                deduped.append(s)
        if self.use_online and len(deduped) < 3:
            for s in self.arxiv.search(topic, max_results=3):
                if s.title.lower() not in seen:
                    deduped.append(s)
        return deduped
