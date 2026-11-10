"""Data-shaping helpers for the Streamlit dashboard.

Everything the dashboard displays that is not raw pipeline output is
shaped here first: evidence-graph JSON loading, claim->source mapping
rows, budget rows, contradiction rows, trace lines. This module is
pure Python on purpose — no streamlit import — so the shaping logic
is unit-tested in ``tests/test_dashboard_helpers.py`` and the app file
stays a thin presentation layer.

The only optional dependency is matplotlib, used solely for the
evidence-graph figure; if it is not installed the figure helper
returns None and the app falls back to the mapping table.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


# ---------------------------------------------------------------- graph

def load_evidence_graph(path: Path | str) -> dict:
    """Load an evidence_graph.json file and check its shape.

    Raises ValueError on a file that parses but is not a graph export,
    so the dashboard fails loudly instead of rendering an empty figure.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "nodes" not in data or "edges" not in data:
        raise ValueError(f"{path} does not look like an evidence graph export")
    return data


def graph_counts(graph: dict) -> dict[str, int]:
    """Node/edge counts split by node type."""
    nodes = graph.get("nodes", [])
    return {
        "nodes": len(nodes),
        "claims": sum(1 for n in nodes if n.get("type") == "claim"),
        "sources": sum(1 for n in nodes if n.get("type") == "source"),
        "edges": len(graph.get("edges", [])),
    }


def claim_source_rows(graph: dict) -> list[dict[str, Any]]:
    """One row per supports edge: claim -> the source behind it.

    This is the table form of the graph — the same information the
    figure draws, in a shape that can be read (and sorted) exactly.
    """
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    rows: list[dict[str, Any]] = []
    for edge in graph.get("edges", []):
        claim_node = nodes.get(edge["to"], {})
        source_node = nodes.get(edge["from"], {})
        rows.append({
            "claim_id": edge["to"],
            "claim": claim_node.get("claim", ""),
            "source_id": edge["from"],
            "source_title": source_node.get("title", ""),
            "credibility": edge.get("weight", source_node.get("credibility")),
        })
    rows.sort(key=lambda r: (r["claim_id"]))
    return rows


def graph_figure(graph: dict, max_claim_chars: int = 60):
    """Draw the bipartite evidence graph with matplotlib.

    Sources down the left, claims down the right, one line per
    supports edge with thickness/alpha scaled by credibility weight.
    Returns a matplotlib Figure, or None if matplotlib is unavailable.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None

    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    sources = [n for n in graph.get("nodes", []) if n.get("type") == "source"]
    claims = [n for n in graph.get("nodes", []) if n.get("type") == "claim"]
    if not sources or not claims:
        return None

    def _y_positions(items: list[dict]) -> dict[str, float]:
        if len(items) == 1:
            return {items[0]["id"]: 0.5}
        return {n["id"]: 1.0 - i / (len(items) - 1) for i, n in enumerate(items)}

    src_y = _y_positions(sources)
    clm_y = _y_positions(claims)
    height = max(4.0, 0.55 * max(len(sources), len(claims)))
    fig, ax = plt.subplots(figsize=(10, height))
    for edge in graph.get("edges", []):
        if edge["from"] not in src_y or edge["to"] not in clm_y:
            continue
        w = float(edge.get("weight") or 0.5)
        ax.plot([0.0, 1.0], [src_y[edge["from"]], clm_y[edge["to"]]],
                color="#4C72B0", alpha=0.25 + 0.6 * w, linewidth=0.6 + 2.0 * w, zorder=1)
    ax.scatter([0.0] * len(sources), [src_y[s["id"]] for s in sources],
               s=70, color="#DD8452", zorder=3)
    ax.scatter([1.0] * len(claims), [clm_y[c["id"]] for c in claims],
               s=45, color="#55A868", zorder=3)
    for s in sources:
        label = f"{s['id']} · {s.get('title', '')}"
        if len(label) > 52:
            label = label[:49] + "..."
        ax.annotate(label, (0.0, src_y[s["id"]]), xytext=(-8, 0),
                    textcoords="offset points", ha="right", va="center", fontsize=8)
    for c in claims:
        label = f"{c['id']} · {c.get('claim', '')}"
        if len(label) > max_claim_chars + 4:
            label = label[:max_claim_chars + 1] + "..."
        ax.annotate(label, (1.0, clm_y[c["id"]]), xytext=(8, 0),
                    textcoords="offset points", ha="left", va="center", fontsize=8)
    ax.set_xlim(-0.62, 1.62)
    ax.set_ylim(-0.06, 1.06)
    ax.axis("off")
    ax.set_title("Evidence graph — sources (left) support claims (right); "
                 "thicker line = higher credibility", fontsize=9)
    fig.tight_layout()
    return fig


# -------------------------------------------------------------- evidence

def evidence_rows(evidence_table: Iterable[dict]) -> list[dict[str, Any]]:
    """Reshape the analyst's evidence table for display."""
    rows = []
    for row in evidence_table:
        source = row["source_id"]
        if row.get("source_title"):
            source = f"{source} — {row['source_title']}"
        rows.append({
            "claim": row["claim"],
            "source": source,
            "credibility": row["credibility"],
        })
    return rows


# -------------------------------------------------------- contradictions

def _credibility_of(source: Any) -> float | None:
    if source is None:
        return None
    if isinstance(source, dict):
        return source.get("credibility")
    return getattr(source, "credibility", None)


def contradiction_rows(contradictions: Iterable[dict],
                       sources: Iterable[Any] = ()) -> list[dict[str, Any]]:
    """Flagged pairs with both sources' credibility attached.

    Credibility is resolved from the run's sources when available;
    the detector's per-claim confidence (which the analyst sets from
    the same credibility score) is the fallback.
    """
    by_id = {}
    for s in sources:
        sid = s.get("source_id") if isinstance(s, dict) else getattr(s, "source_id", None)
        if sid:
            by_id[sid] = s
    rows = []
    for c in contradictions:
        cred_a = _credibility_of(by_id.get(c["source_a"]))
        cred_b = _credibility_of(by_id.get(c["source_b"]))
        rows.append({
            "claim_a": c["claim_a"],
            "source_a": c["source_a"],
            "credibility_a": cred_a if cred_a is not None else c.get("confidence_a"),
            "claim_b": c["claim_b"],
            "source_b": c["source_b"],
            "credibility_b": cred_b if cred_b is not None else c.get("confidence_b"),
            "concept": c.get("concept", ", ".join(c.get("shared_terms", []))),
        })
    return rows


# --------------------------------------------------------------- budget

def budget_rows(budget_summary: dict) -> list[dict[str, Any]]:
    """Per-agent budget rows from BudgetTracker.summary(), costliest first."""
    by_agent = budget_summary.get("by_agent", {})
    spent = float(budget_summary.get("spent_usd", 0.0))
    rows = []
    for agent, entry in by_agent.items():
        cost = float(entry.get("cost_usd", 0.0))
        rows.append({
            "agent": agent,
            "calls": int(entry.get("calls", 0)),
            "input_tokens": int(entry.get("input_tokens", 0)),
            "output_tokens": int(entry.get("output_tokens", 0)),
            "cost_usd": round(cost, 6),
            "share_pct": round(100.0 * cost / spent, 1) if spent > 0 else 0.0,
        })
    rows.sort(key=lambda r: -r["cost_usd"])
    return rows


def budget_totals(budget_summary: dict) -> dict[str, Any]:
    """Run-level budget figures for the summary strip."""
    spent = float(budget_summary.get("spent_usd", 0.0))
    budget = float(budget_summary.get("budget_usd", 0.0))
    return {
        "spent_usd": round(spent, 6),
        "budget_usd": budget,
        "remaining_usd": round(budget - spent, 6),
        "used_pct": round(100.0 * spent / budget, 2) if budget > 0 else 0.0,
    }


# ---------------------------------------------------------------- trace

def trace_lines(trace: Iterable[dict]) -> list[str]:
    """Format trace events the way the CLI prints them."""
    lines = []
    for e in trace:
        line = f"[{e.get('t_ms', 0)}ms] {e.get('agent', '?')}: {e.get('action', '')}"
        if e.get("detail"):
            line += f" — {e['detail']}"
        lines.append(line)
    return lines
