"""Evidence graph + contradiction detection.

The planted-pair tests pin the heuristic's contract: opposing polarity
over at least three shared content terms, from different sources, is a
flag; agreement or same-source nuance is not.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research_team.agents.analyst import AnalystAgent
from research_team.cli import main as cli_main
from research_team.config import Settings
from research_team.evidence_graph import build_evidence_graph, detect_contradictions
from research_team.state import Finding, Source
from research_team.supervisor import Supervisor


def _small_state():
    sources = [
        Source(source_id="S1", title="Paper one", source_type="journal", year=2024,
               key_points=["Point one from paper one", "Point two from paper one"]),
        Source(source_id="S2", title="Paper two", source_type="blog", year=2022,
               key_points=["Only point from paper two"]),
    ]
    findings, evidence = AnalystAgent().run(sources)
    return sources, findings, evidence


def test_graph_node_and_edge_counts_from_small_state():
    sources, findings, evidence = _small_state()
    graph = build_evidence_graph(evidence, sources)
    claim_nodes = [n for n in graph["nodes"] if n["type"] == "claim"]
    source_nodes = [n for n in graph["nodes"] if n["type"] == "source"]
    assert len(claim_nodes) == 3          # one node per evidence row
    assert len(source_nodes) == 2
    assert len(graph["edges"]) == 3       # every claim supported exactly once here
    assert all(e["relation"] == "supports" for e in graph["edges"])
    by_pair = {(e["from"], e["to"]): e["weight"] for e in graph["edges"]}
    assert by_pair[("S1", "F1")] == sources[0].credibility
    assert source_nodes[0]["title"] == "Paper one"


def test_contradiction_flags_planted_opposing_pair():
    findings = [
        Finding(claim="Explanations improved clinician trust in the imaging system",
                source_ids=["S1"]),
        Finding(claim="Explanations did not improve clinician trust in the imaging system",
                source_ids=["S2"]),
    ]
    flags = detect_contradictions(findings)
    assert len(flags) == 1
    assert {flags[0]["source_a"], flags[0]["source_b"]} == {"S1", "S2"}
    for term in ("clinician", "trust", "imaging"):
        assert term in flags[0]["shared_terms"]


def test_contradiction_does_not_flag_agreeing_pair():
    findings = [
        Finding(claim="Explanations improved clinician trust in the imaging system",
                source_ids=["S1"]),
        Finding(claim="Explanations improved clinician trust and clinician confidence",
                source_ids=["S2"]),
    ]
    assert detect_contradictions(findings) == []


def test_contradiction_does_not_flag_same_source_pair():
    findings = [
        Finding(claim="Saliency maps alone did not measurably increase clinician trust",
                source_ids=["S1"]),
        Finding(claim="Saliency maps alone measurably increased clinician trust",
                source_ids=["S1"]),
    ]
    assert detect_contradictions(findings) == []


def test_end_to_end_report_surfaces_fixture_contradiction():
    sup = Supervisor(Settings())
    state = sup.run("explainable AI in healthcare", save=False)
    assert len(state.contradictions) == 1
    flag = state.contradictions[0]
    assert {flag["source_a"], flag["source_b"]} == {"S1", "S13"}
    assert "## Conflicting Evidence" in state.draft
    section = state.draft.split("## Conflicting Evidence")[1].split("## ")[0]
    assert "Saliency maps alone did not measurably increase clinician trust" in section
    assert "Saliency maps alone measurably increased clinician trust" in section
    # The critique carries the flag, and approval is not blocked by it.
    assert state.critique is not None and state.critique.approved
    assert state.critique.contradictions == state.contradictions
    assert any("Conflicting evidence" in c for c in state.critique.comments)
    # Graph in state matches the run: claim nodes = evidence rows.
    claim_nodes = [n for n in state.evidence_graph["nodes"] if n["type"] == "claim"]
    assert len(claim_nodes) == len(state.evidence_table)
    assert len(state.evidence_graph["edges"]) == len(state.evidence_table)


def test_topic_without_tension_omits_conflicting_evidence_section():
    sup = Supervisor(Settings())
    state = sup.run("LLM agents and multi-agent systems", save=False)
    assert state.contradictions == []
    assert "## Conflicting Evidence" not in state.draft


def test_cli_writes_evidence_graph_alongside_report(tmp_path):
    out = tmp_path / "report.md"
    assert cli_main(["explainable AI in healthcare", "-o", str(out)]) == 0
    graph_file = tmp_path / "evidence_graph.json"
    assert graph_file.exists()
    graph = json.loads(graph_file.read_text(encoding="utf-8"))
    assert graph["nodes"] and graph["edges"]
    assert "## Conflicting Evidence" in out.read_text(encoding="utf-8")
