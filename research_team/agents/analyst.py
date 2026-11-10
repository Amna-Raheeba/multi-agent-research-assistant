"""Analyst agent: turn sources into findings + an evidence table.

Credibility scoring is a heuristic and is labelled as such everywhere
it surfaces. It exists to stop a blog post and a journal paper counting
the same in the final report.
"""
from __future__ import annotations

from ..state import Finding, Source

BASE_SCORE = {"journal": 0.9, "conference": 0.8, "report": 0.65, "preprint": 0.6, "blog": 0.3}


def score_credibility(source: Source, current_year: int = 2026) -> float:
    score = BASE_SCORE.get(source.source_type, 0.5)
    if source.year:
        age = max(0, current_year - source.year)
        score -= min(0.15, age * 0.03)  # old preprints/blogs decay; journals already high
        if age <= 1:
            score += 0.03
    if not source.url and source.source_type in {"preprint", "blog"}:
        score -= 0.05
    return round(max(0.05, min(0.97, score)), 2)


class AnalystAgent:
    name = "analyst"

    def run(self, sources: list[Source]):
        findings: list[Finding] = []
        evidence: list[dict] = []
        for src in sources:
            src.credibility = score_credibility(src)
            for point in src.key_points:
                findings.append(Finding(claim=point, source_ids=[src.source_id],
                                        confidence=src.credibility))
                evidence.append({
                    "claim": point,
                    "source_id": src.source_id,
                    "source_title": src.title,
                    "credibility": src.credibility,
                    "support": "stated in source key points",
                })
        # Strongest evidence first — the writer drafts from the top.
        findings.sort(key=lambda f: -f.confidence)
        evidence.sort(key=lambda e: -e["credibility"])
        return findings, evidence
