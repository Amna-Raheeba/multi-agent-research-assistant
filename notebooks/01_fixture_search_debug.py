"""Why does a source rank for a topic — and why does another one not?

Question (4 Nov 2026): when I added a new fixture source it showed up
under a topic it does not belong to. This script breaks the fixture
search score down per source so the ranking stops being a black box:
concept groups hit, expanded-token overlap, and title overlap — the
three ingredients of the score in FixtureSearch.search().

It also prints the near-misses: sources that were considered but
filtered out by the two-concept rule, with the reason.

Run from the project root:  python notebooks/01_fixture_search_debug.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research_team.config import DEFAULT_FIXTURES  # noqa: E402
from research_team.tools.search_tools import (  # noqa: E402
    FixtureSearch, _concepts_hit, _expand, _query_concepts, _tokens,
)

TOPICS = [
    "explainable AI in healthcare",
    "explainable predictive maintenance",
]


def explain(search: FixtureSearch, topic: str) -> None:
    raw_q = _tokens(topic)
    q = _expand(raw_q)
    concepts = _query_concepts(raw_q)
    returned = {s.source_id for s in search.search(topic, max_results=8)}
    print(f"\n== {topic} ==")
    print(f"query concepts: {concepts} (a source needs >= 2 when the query has >= 2)")
    for src in search.sources:
        haystack = _tokens(
            f"{src.title} {src.summary} {' '.join(src.key_points)} "
            f"{' '.join(src.keywords)} {src.venue}")
        hits = _concepts_hit(raw_q, haystack)
        overlap = len(q & haystack)
        title_overlap = len(q & _tokens(src.title))
        score = hits * 10 + overlap + 1.5 * title_overlap
        status = "RETURNED" if src.source_id in returned else "filtered"
        reason = ""
        if src.source_id not in returned:
            reason = (f" — only {hits} concept group(s) hit"
                      if len(concepts) >= 2 and hits < 2 else " — score below cut")
        print(f"  [{src.source_id:>4}] {status:>8}  score={score:5.1f} "
              f"concepts={hits} overlap={overlap:2d} title_overlap={title_overlap}{reason}")


if __name__ == "__main__":
    search = FixtureSearch(DEFAULT_FIXTURES)
    for topic in TOPICS:
        explain(search, topic)
