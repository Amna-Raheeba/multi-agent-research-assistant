"""Fixture evaluation — labelled as fixture evaluation, not a benchmark.

Runs the full pipeline on three fixture topics and reports:
- section completeness (required headings present)
- citation coverage (findings cited in Key Findings / total findings)
- evidence coverage (findings present in the evidence table)
Numbers describe this small, hand-written corpus only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from research_team.config import Settings  # noqa: E402
from research_team.supervisor import Supervisor  # noqa: E402

FIXTURE_TOPICS = [
    "explainable AI in healthcare",
    "LLM agents and multi-agent systems",
    "explainable predictive maintenance",
]
REQUIRED_SECTIONS = ["Executive Summary", "Key Findings", "Evidence Table", "Discussion", "Limitations", "References"]


def evaluate_topic(topic: str, supervisor: Supervisor | None = None) -> dict:
    sup = supervisor or Supervisor(Settings(offline=True))
    state = sup.run(topic, save=False)
    draft = state.draft
    sections = [s for s in REQUIRED_SECTIONS if f"## {s}" in draft]
    # Count cited bullets in Key Findings only: the Conflicting Evidence
    # section also quotes cited claims, and counting those pushed this
    # ratio above 1.0 — a coverage figure over 100% is a bug, not a result.
    kf = draft.split("## Key Findings", 1)[-1].split("\n## ", 1)[0]
    cited = len(re.findall(r"^- .+ \[[A-Z]+\d+", kf, flags=re.M))
    total = len(state.findings)
    return {
        "topic": topic,
        "sources": len(state.sources),
        "findings": total,
        "section_completeness": round(len(sections) / len(REQUIRED_SECTIONS), 2),
        "citation_coverage": round(cited / total, 2) if total else 0.0,
        "evidence_coverage": round(len(state.evidence_table) / total, 2) if total else 0.0,
        "critic_approved": bool(state.critique and state.critique.approved),
        "revisions": state.revision_count,
        "estimated_cost_usd": sup.budget.summary()["spent_usd"],
    }


def main() -> None:
    results = [evaluate_topic(t) for t in FIXTURE_TOPICS]
    for r in results:
        print(r)
    avg = lambda k: round(sum(r[k] for r in results) / len(results), 2)  # noqa: E731
    print(f"\nMean section completeness: {avg('section_completeness')}")
    print(f"Mean citation coverage:    {avg('citation_coverage')}")
    print("Note: fixture evaluation on a small hand-written corpus — not a general benchmark.")


if __name__ == "__main__":
    main()
