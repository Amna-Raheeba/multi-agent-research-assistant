"""Tests for dashboard/helpers.py — the dashboard's shaping logic.

The helpers module is loaded by file path because ``dashboard/`` is
not a package (Streamlit apps are run as scripts). Loading it this
way also proves the module has no streamlit import: this test run
has no streamlit installed.
"""
import importlib.util
import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "dashboard_helpers", PROJECT_ROOT / "dashboard" / "helpers.py")
helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(helpers)

from research_team.state import Source  # noqa: E402


def test_load_example_graph_and_counts():
    graph = helpers.load_evidence_graph(PROJECT_ROOT / "examples" / "evidence_graph.json")
    counts = helpers.graph_counts(graph)
    assert counts["nodes"] == len(graph["nodes"])
    assert counts["edges"] == len(graph["edges"])
    assert counts["claims"] > 0 and counts["sources"] > 0
    assert counts["claims"] + counts["sources"] == counts["nodes"]


def test_load_evidence_graph_rejects_non_graph(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"hello": "world"}), encoding="utf-8")
    try:
        helpers.load_evidence_graph(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for a non-graph JSON file")


def test_claim_source_rows_match_edges():
    graph = helpers.load_evidence_graph(PROJECT_ROOT / "examples" / "evidence_graph.json")
    rows = helpers.claim_source_rows(graph)
    assert len(rows) == len(graph["edges"])
    source_cred = {n["id"]: n["credibility"] for n in graph["nodes"] if n["type"] == "source"}
    for row in rows:
        assert row["claim"]  # every edge lands on a real claim node
        assert row["source_title"]  # and starts from a real source node
        assert row["credibility"] == source_cred[row["source_id"]]


def test_budget_rows_and_totals():
    summary = {
        "budget_usd": 0.25,
        "spent_usd": 0.003,
        "by_agent": {
            "writer": {"input_tokens": 100, "output_tokens": 400, "cost_usd": 0.002, "calls": 2},
            "researcher": {"input_tokens": 50, "output_tokens": 200, "cost_usd": 0.001, "calls": 1},
        },
    }
    rows = helpers.budget_rows(summary)
    assert [r["agent"] for r in rows] == ["writer", "researcher"]  # costliest first
    assert abs(sum(r["share_pct"] for r in rows) - 100.0) < 0.2
    totals = helpers.budget_totals(summary)
    assert totals["spent_usd"] == 0.003
    assert totals["remaining_usd"] == 0.247
    assert totals["used_pct"] == 1.2


def test_contradiction_rows_resolve_credibility_from_sources():
    sources = [
        Source(source_id="S1", title="A", credibility=0.84),
        Source(source_id="S13", title="B", credibility=0.8),
    ]
    contradictions = [{
        "claim_a": "Saliency maps alone did not measurably increase clinician trust",
        "source_a": "S1", "confidence_a": 0.84,
        "claim_b": "Saliency maps alone measurably increased clinician trust",
        "source_b": "S13", "confidence_b": 0.8,
        "shared_terms": ["saliency", "maps", "clinician", "trust"],
        "concept": "saliency, maps, clinician, trust",
    }]
    rows = helpers.contradiction_rows(contradictions, sources)
    assert len(rows) == 1
    assert rows[0]["credibility_a"] == 0.84
    assert rows[0]["credibility_b"] == 0.8
    assert rows[0]["concept"].startswith("saliency")


def test_evidence_rows_and_trace_lines():
    rows = helpers.evidence_rows([
        {"claim": "X works", "source_id": "S2", "source_title": "Paper X", "credibility": 0.9},
        {"claim": "Y fails", "source_id": "S5", "source_title": "", "credibility": 0.6},
    ])
    assert rows[0]["source"] == "S2 — Paper X"
    assert rows[1]["source"] == "S5"
    lines = helpers.trace_lines([
        {"t_ms": 12, "agent": "critic", "action": "review", "detail": "approved=True"},
        {"t_ms": 30, "agent": "supervisor", "action": "route", "detail": ""},
    ])
    assert lines[0] == "[12ms] critic: review — approved=True"
    assert lines[1] == "[30ms] supervisor: route"


def test_graph_figure_builds_from_example_graph():
    # matplotlib is dashboard-only: in a bare CI env (pytest only) the helper
    # returns None by design, so skip there instead of failing.
    pytest.importorskip("matplotlib")
    graph = helpers.load_evidence_graph(PROJECT_ROOT / "examples" / "evidence_graph.json")
    fig = helpers.graph_figure(graph)
    assert fig is not None
    assert len(fig.axes) == 1
