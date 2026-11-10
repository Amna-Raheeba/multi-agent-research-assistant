"""arXiv API tool (optional, online only).

Parses the Atom feed with stdlib XML. Returns [] on any failure —
callers should treat arXiv as an enrichment source, not a dependency.
"""
from __future__ import annotations

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from ..state import Source

_NS = {"atom": "http://www.w3.org/2005/Atom"}


class ArxivSearch:
    def search(self, query: str, max_results: int = 5) -> list[Source]:
        params = urllib.parse.urlencode({"search_query": f"all:{query}", "max_results": max_results})
        try:
            with urllib.request.urlopen(f"https://export.arxiv.org/api/query?{params}", timeout=15) as resp:
                root = ET.fromstring(resp.read())
        except Exception:
            return []
        out: list[Source] = []
        for i, entry in enumerate(root.findall("atom:entry", _NS), start=1):
            title = (entry.findtext("atom:title", default="", namespaces=_NS) or "").strip().replace("\n", " ")
            summary = (entry.findtext("atom:summary", default="", namespaces=_NS) or "").strip()
            authors = [a.findtext("atom:name", default="", namespaces=_NS) for a in entry.findall("atom:author", _NS)]
            published = entry.findtext("atom:published", default="", namespaces=_NS) or ""
            out.append(Source(source_id=f"AX{i}", title=title, authors=authors,
                              year=int(published[:4]) if published[:4].isdigit() else None,
                              venue="arXiv preprint", source_type="preprint",
                              url=entry.findtext("atom:id", default="", namespaces=_NS) or "",
                              summary=summary[:600], key_points=[]))
        return out
