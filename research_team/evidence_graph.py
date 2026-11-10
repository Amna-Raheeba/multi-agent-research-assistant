"""Evidence graph + contradiction detection.

The evidence table is flat: claim, source, credibility. Flattening loses
structure a reader actually wants — which claims hang off which source,
and whether two sources pull in opposite directions on the same point.
This module rebuilds that structure as a bipartite graph and scans it
for conflicts.

Graph shape
-----------
Nodes are claims (``F1``, ``F2``, ... in evidence-table order) and
sources (``S1``, ``S2``, ...). An edge ``source -> claim`` with
``relation="supports"`` carries the source's credibility as its weight.
The graph is exported to ``evidence_graph.json`` on every CLI run so it
can be inspected or loaded into a graph tool without re-running the
pipeline.

Contradiction detection (heuristic — read this before trusting it)
------------------------------------------------------------------
Two findings from *different* sources are flagged when:

1. they share at least ``MIN_SHARED_TERMS`` (3) content terms after
   stopword and polarity words are removed, and
2. their polarity differs: one carries an explicit negation/contrast
   marker (``did not``, ``ignored``, ``disagree`` ...) and no positive
   marker, the other carries a positive outcome marker (``improved``,
   ``increased``, ``helped`` ...) and no negation.

That is deliberately narrow. It catches the blunt case — "saliency maps
did not increase trust" vs "saliency maps increased trust" — and misses
paraphrased or subtle disagreement entirely. A mixed claim (both kinds
of marker) counts as neutral and is never flagged. Findings from the
same source are never paired: a single paper can hold a nuanced
position without contradicting itself here.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .state import Finding, Source

MIN_SHARED_TERMS = 3

STOPWORDS = {
    "a", "an", "the", "in", "of", "for", "and", "or", "to", "on", "with",
    "by", "at", "from", "was", "were", "are", "is", "be", "been", "than",
    "that", "this", "it", "its", "as", "into", "both", "when", "while",
}

# Polarity vocabulary. These words decide direction, so they are also
# excluded from the shared-term count — otherwise "improved" vs
# "did not improve" would score as agreement on the verb itself.
# Negated phrases are checked first: in "did not increase", the verb
# being negated is exactly the positive marker, so phrase-level
# negation takes precedence over single-token counting.
NEGATION_PHRASES = {
    "did not", "does not", "do not", "didn't", "doesn't",
    "not measurably", "no measurable", "failed to", "turned off",
}
NEGATION_TOKENS = {
    "never", "cannot", "ignored", "disagree", "disagreement",
    "failed", "fails", "without",
}
POSITIVE_MARKERS = {
    "improved", "improve", "improves", "increased", "increase", "increases",
    "helped", "helps", "valued", "rated", "useful", "effective", "better",
    "raised",
}
POLARITY_WORDS = (
    NEGATION_TOKENS | POSITIVE_MARKERS
    | {"did", "does", "do", "not", "no", "alone"}
)


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def _content_terms(text: str) -> list[str]:
    """Content terms in claim order, deduplicated, polarity-free."""
    seen: list[str] = []
    for tok in _tokens(text):
        if tok in STOPWORDS or tok in POLARITY_WORDS or len(tok) <= 2:
            continue
        if tok not in seen:
            seen.append(tok)
    return seen


def _polarity(text: str) -> str:
    toks = _tokens(text)
    if any(p in " ".join(toks) for p in NEGATION_PHRASES):
        return "negative"
    tok_set = set(toks)
    neg = bool(tok_set & NEGATION_TOKENS)
    pos = bool(tok_set & POSITIVE_MARKERS)
    if neg and not pos:
        return "negative"
    if pos and not neg:
        return "positive"
    return "neutral"  # includes the mixed case, on purpose


def build_evidence_graph(evidence_table: list[dict],
                         sources: list[Source] | None = None) -> dict:
    """Build the claim<->source bipartite graph from the evidence table."""
    by_id = {s.source_id: s for s in (sources or [])}
    nodes: list[dict] = []
    edges: list[dict] = []
    seen_sources: set[str] = set()

    for i, row in enumerate(evidence_table, start=1):
        claim_id = f"F{i}"
        nodes.append({
            "id": claim_id,
            "type": "claim",
            "claim": row["claim"],
            "source_ids": [row["source_id"]],
        })
        sid = row["source_id"]
        if sid not in seen_sources:
            seen_sources.add(sid)
            src = by_id.get(sid)
            nodes.append({
                "id": sid,
                "type": "source",
                "title": src.title if src else row.get("source_title", ""),
                "credibility": row["credibility"],
                "source_type": src.source_type if src else "",
                "year": src.year if src else None,
            })
        edges.append({
            "from": sid,
            "to": claim_id,
            "relation": "supports",
            "weight": row["credibility"],
        })
    return {"nodes": nodes, "edges": edges}


def detect_contradictions(findings: list[Finding]) -> list[dict]:
    """Flag opposing-polarity finding pairs about the same concept.

    See the module docstring for the exact (narrow) heuristic.
    """
    prepared = [
        (f, _content_terms(f.claim), _polarity(f.claim)) for f in findings
    ]
    flags: list[dict] = []
    for i in range(len(prepared)):
        for j in range(i + 1, len(prepared)):
            a, terms_a, pol_a = prepared[i]
            b, terms_b, pol_b = prepared[j]
            if not a.source_ids or not b.source_ids:
                continue
            if a.source_ids[0] == b.source_ids[0]:
                continue  # same source: nuance, not contradiction
            if {pol_a, pol_b} != {"positive", "negative"}:
                continue
            shared = [t for t in terms_a if t in set(terms_b)]
            if len(shared) < MIN_SHARED_TERMS:
                continue
            flags.append({
                "claim_a": a.claim,
                "source_a": a.source_ids[0],
                "confidence_a": a.confidence,
                "claim_b": b.claim,
                "source_b": b.source_ids[0],
                "confidence_b": b.confidence,
                "shared_terms": shared,
                "concept": ", ".join(shared),
                "reason": (
                    f"opposing polarity over shared terms ({', '.join(shared)}): "
                    f"[{a.source_ids[0]}] is {pol_a}, [{b.source_ids[0]}] is {pol_b}"
                ),
            })
    return flags


def analyse_evidence(evidence_table: list[dict], findings: list[Finding],
                     sources: list[Source] | None = None) -> tuple[dict, list[dict]]:
    """Convenience wrapper used by the supervisor: graph + contradictions."""
    return build_evidence_graph(evidence_table, sources), detect_contradictions(findings)


def write_evidence_graph(graph: dict, path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph, indent=2), encoding="utf-8")
    return path
