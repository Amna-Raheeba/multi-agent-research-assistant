"""Shared state passed between agents.

A single dataclass instead of a dict: typos in field names fail fast,
and the checkpointer can serialise it without guessing a schema.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Source:
    source_id: str
    title: str
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    venue: str = ""
    source_type: str = "preprint"  # journal | conference | preprint | report | blog
    url: str = ""
    summary: str = ""
    key_points: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    credibility: float = 0.0  # filled in by the analyst, 0..1

    def citation(self) -> str:
        authors = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            authors += " et al."
        return f"{authors} ({self.year}). {self.title}. {self.venue}.".strip()


@dataclass
class Finding:
    claim: str
    source_ids: list[str]
    confidence: float = 0.5
    note: str = ""


@dataclass
class Critique:
    approved: bool
    unsupported_claims: list[str] = field(default_factory=list)
    missing_citations: int = 0
    comments: list[str] = field(default_factory=list)


@dataclass
class ResearchState:
    topic: str
    phase: str = "init"  # init|research|analysis|writing|critique|revision|done|failed
    sources: list[Source] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    evidence_table: list[dict[str, Any]] = field(default_factory=list)
    draft: str = ""
    critique: Critique | None = None
    revision_count: int = 0
    iteration: int = 0
    errors: list[str] = field(default_factory=list)
    status: str = "running"  # running|complete|budget_exceeded|max_iterations|failed
    trace: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResearchState":
        sources = [Source(**s) for s in data.pop("sources", [])]
        findings = [Finding(**f) for f in data.pop("findings", [])]
        critique_data = data.pop("critique", None)
        critique = Critique(**critique_data) if critique_data else None
        state = cls(**data)
        state.sources, state.findings, state.critique = sources, findings, critique
        return state
