"""Search tools: offline fixtures first, online sources optional.

Offline is the default because a research tool that only works when the
network and a third-party HTML layout cooperate is not a reliable tool.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

from ..state import Source

STOPWORDS = {"a", "an", "the", "in", "of", "for", "and", "or", "to", "on", "with", "how", "why", "what", "is", "are"}


# Small, explicit synonym map. A real system would use embeddings;
# for a fixture corpus this is transparent and testable, and it avoids
# pretending a keyword search is semantic search.
SYNONYMS = {
    "healthcare": {"medical", "clinical", "hospital", "clinician", "clinicians", "patient", "patients", "radiologists"},
    "explainable": {"explanation", "explanations", "attribution", "interpretability", "counterfactual", "counterfactuals", "fidelity"},
    "explanations": {"explainable", "attribution", "counterfactual"},
    "agents": {"agent", "multi", "supervisor", "orchestration", "tool"},
    "agent": {"agents", "supervisor", "orchestration", "tool"},
    "maintenance": {"predictive", "failure", "degradation", "machinery", "phm", "repair"},
    "predictive": {"maintenance", "failure", "degradation"},
    "llm": {"language", "model", "models"},
}


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOPWORDS and len(t) > 2}


def _expand(tokens: set[str]) -> set[str]:
    expanded = set(tokens)
    for t in tokens:
        expanded |= SYNONYMS.get(t, set())
    return expanded


# Clean concept groups for the multi-concept filter. Groups do not
# overlap, so one word in a source cannot satisfy two query concepts.
CONCEPT_GROUPS = {
    "healthcare": {"healthcare", "medical", "clinical", "hospital", "clinician", "clinicians"},
    "explainable": {"explainable", "explanation", "explanations", "attribution", "counterfactual", "counterfactuals"},
    "agents": {"agent", "agents", "supervisor", "orchestration"},
    "llm": {"llm", "llms"},
    "maintenance": {"maintenance", "machinery", "degradation", "turbofan", "repair"},
    "predictive": {"predictive", "prediction", "prognostics"},
}


def _query_concepts(raw_q: set[str]) -> list[str]:
    return [name for name, words in CONCEPT_GROUPS.items() if raw_q & words]


def _concepts_hit(raw_q: set[str], haystack: set[str]) -> int:
    return sum(1 for name in _query_concepts(raw_q) if haystack & CONCEPT_GROUPS[name])


class FixtureSearch:
    """Keyword-overlap search over data/fixtures.json."""

    def __init__(self, fixtures_path: Path):
        raw = json.loads(Path(fixtures_path).read_text(encoding="utf-8"))
        self.sources = [Source(**s) for s in raw["sources"]]

    def search(self, query: str, max_results: int = 8) -> list[Source]:
        raw_q = _tokens(query)
        q = _expand(raw_q)
        if not q:
            return []
        scored: list[tuple[float, Source]] = []
        for src in self.sources:
            haystack = _tokens(f"{src.title} {src.summary} {' '.join(src.key_points)} {' '.join(src.keywords)} {src.venue}")
            overlap = len(q & haystack)
            if overlap == 0:
                continue
            # Require a hit on at least two distinct query concepts when the
            # query spans several — stops a maintenance paper with only the word
            # 'explainable' outranking actual healthcare papers.
            concepts_hit = _concepts_hit(raw_q, haystack)
            if len(_query_concepts(raw_q)) >= 2 and concepts_hit < 2:
                continue
            title_overlap = len(q & _tokens(src.title))
            score = concepts_hit * 10 + overlap + 1.5 * title_overlap
            scored.append((score, src))
        scored.sort(key=lambda x: (-x[0], x[1].source_id))
        return [s for _, s in scored[:max_results]]


class _DDGParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results: list[str] = []
        self._capture = False

    def handle_starttag(self, tag, attrs):
        self._capture = dict(attrs).get("class") == "result__a"

    def handle_data(self, data):
        if self._capture and data.strip():
            self.results.append(data.strip())
            self._capture = False


class DuckDuckGoSearch:
    """Best-effort DuckDuckGo HTML search. Never raises on network failure."""

    def search_titles(self, query: str, max_results: int = 5) -> list[str]:
        url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "research-team/0.2"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                parser = _DDGParser()
                parser.feed(resp.read().decode("utf-8", errors="ignore"))
            return parser.results[:max_results]
        except Exception:
            return []
