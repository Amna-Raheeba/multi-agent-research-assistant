"""Writer agent: draft a structured report from findings only.

Rule the writer lives by: every finding sentence carries a citation
marker like [S2]. Sentences without evidence do not get written —
except in the deliberately flawed first pass used to exercise the
critic in tests, which is not the production path.
"""
from __future__ import annotations

from ..state import Finding, Source


class WriterAgent:
    name = "writer"

    def run(self, topic: str, findings: list[Finding], sources: list[Source],
            evidence_table: list[dict]) -> str:
        return self._render(topic, findings, sources, evidence_table)

    def revise(self, topic: str, findings: list[Finding], sources: list[Source],
               evidence_table: list[dict], unsupported: list[str]) -> str:
        """Revision = re-render from evidence only.

        Unsupported sentences were never generated from findings, so
        re-rendering from findings drops them by construction rather
        than trying to patch the old draft in place.
        """
        return self._render(topic, findings, sources, evidence_table)

    def _render(self, topic, findings, sources, evidence_table) -> str:
        by_id = {s.source_id: s for s in sources}
        lines: list[str] = []
        lines.append(f"# Research Report: {topic}")
        lines.append("")
        lines.append("## Executive Summary")
        top = findings[:3]
        if top:
            summary = " ".join(f"{f.claim} [{', '.join(f.source_ids)}]." for f in top)
            lines.append(f"This report synthesises {len(sources)} sources on {topic}. {summary}")
        else:
            lines.append(f"No sources were found for {topic} in the searched collection.")
        lines.append("")
        lines.append("## Key Findings")
        for f in findings:
            lines.append(f"- {f.claim} [{', '.join(f.source_ids)}]")
        lines.append("")
        lines.append("## Evidence Table")
        lines.append("| Claim | Source | Credibility |")
        lines.append("|---|---|---|")
        for row in evidence_table:
            claim = row["claim"].replace("|", "/")
            lines.append(f"| {claim} | {row['source_id']} | {row['credibility']:.2f} |")
        lines.append("")
        lines.append("## Discussion")
        if findings:
            lines.append(
                "The findings above are limited to what the collected sources state. "
                "Higher-credibility sources should weigh more heavily where findings conflict, "
                "and no claim in this report extends beyond a cited source."
            )
        else:
            lines.append("No evidence was available to discuss.")
        lines.append("")
        lines.append("## Limitations")
        lines.append("- Source collection is limited to the searched corpus; this is not a systematic review.")
        lines.append("- Credibility scores are a simple heuristic based on source type and age, not peer review of each paper.")
        lines.append("- Summaries in the corpus are short, so nuance from full texts may be missing.")
        lines.append("")
        lines.append("## References")
        for s in sources:
            lines.append(f"- [{s.source_id}] {s.citation()}")
        lines.append("")
        return "\n".join(lines)
