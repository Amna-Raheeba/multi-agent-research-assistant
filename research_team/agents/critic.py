"""Critic agent: check the draft against the evidence table.

Two checks, both mechanical on purpose:
1. Every bullet in Key Findings must carry a citation marker.
2. Every cited claim must exist in the evidence table — a sentence
   that cites [S9] for a claim S9 never made still fails here if the
   claim text is injected without a matching finding.

An LLM judge would be more flexible and far less predictable in tests.
"""
from __future__ import annotations

import re

from ..state import Critique, Finding

CITATION_RE = re.compile(r"\[([A-Z]+\d+(?:,\s*[A-Z]+\d+)*)\]")


class CriticAgent:
    name = "critic"

    def run(self, draft: str, findings: list[Finding]) -> Critique:
        known_claims = {f.claim.strip().lower() for f in findings}
        unsupported: list[str] = []
        missing = 0

        in_findings = False
        for line in draft.splitlines():
            if line.startswith("## Key Findings"):
                in_findings = True
                continue
            if line.startswith("## ") and in_findings:
                in_findings = False
            if not in_findings or not line.strip().startswith("- "):
                continue
            body = line.strip()[2:].strip()
            if not CITATION_RE.search(body):
                missing += 1
                unsupported.append(body)
                continue
            claim = CITATION_RE.sub("", body).strip().rstrip(".")
            if claim.lower() not in known_claims:
                unsupported.append(body)

        comments = []
        if unsupported:
            comments.append(f"{len(unsupported)} unsupported or uncited claim(s) in Key Findings.")
        if missing:
            comments.append(f"{missing} claim(s) missing a citation marker.")
        return Critique(approved=not unsupported, unsupported_claims=unsupported,
                        missing_citations=missing, comments=comments)
