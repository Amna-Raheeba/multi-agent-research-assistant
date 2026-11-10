import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research_team.agents.analyst import score_credibility
from research_team.agents.critic import CriticAgent
from research_team.config import Settings
from research_team.state import Finding, ResearchState, Source
from research_team.supervisor import BudgetTracker, Supervisor


def make_supervisor(**overrides):
    settings = Settings(**overrides)
    return Supervisor(settings)


def test_supervisor_routing_follows_phases():
    sup = make_supervisor()
    state = ResearchState(topic="explainable AI in healthcare")
    assert sup.decide_next(state) == "researcher"
    state.phase = "research"
    assert sup.decide_next(state) == "analyst"
    state.phase = "analysis"
    assert sup.decide_next(state) == "writer"
    state.phase = "writing"
    assert sup.decide_next(state) == "critic"
    state.phase = "done"
    assert sup.decide_next(state) is None


def test_supervisor_routing_stops_at_max_iterations():
    sup = make_supervisor(max_iterations=3)
    state = ResearchState(topic="x", phase="init", iteration=3)
    assert sup.decide_next(state) is None


def test_budget_tracker_accumulates_per_agent():
    tracker = BudgetTracker(budget_usd=1.0)
    tracker.record("researcher", "a " * 500, "b " * 500)
    tracker.record("researcher", "a " * 500, "b " * 500)
    summary = tracker.summary()
    assert summary["by_agent"]["researcher"]["calls"] == 2
    assert summary["spent_usd"] > 0


def test_budget_guard_stops_loop():
    sup = make_supervisor(budget_usd=0.000001)
    state = sup.run("explainable AI in healthcare", save=False)
    # Either the guard trips during the run, or the tiny budget is exceeded by the end.
    assert sup.budget.exceeded
    assert state.status == "budget_exceeded" or sup.budget.spent_usd > sup.budget.budget_usd


def test_critic_rejects_uncited_claim():
    critic = CriticAgent()
    findings = [Finding(claim="Explanations paired with confidence improved appropriate reliance", source_ids=["S1"])]
    draft = "## Key Findings\n- Hospitals should deploy this everywhere immediately.\n\n## Discussion\nx"
    critique = critic.run(draft, findings)
    assert not critique.approved
    assert critique.missing_citations == 1


def test_critic_triggers_revision_on_unsupported_claim():
    """A cited but fabricated claim must still fail, then a revision fixes the run."""
    sup = make_supervisor()
    state = sup.run("explainable AI in healthcare", save=False)
    assert state.critique is not None
    # Inject an unsupported claim into a fresh draft and confirm the critic flags it,
    # which is exactly the condition supervisor uses to route to writer_revision.
    bad_draft = state.draft.replace(
        "## Discussion",
        "## Key Findings\n- This treatment cures all patients in 24 hours [S1].\n\n## Discussion",
    )
    critique = CriticAgent().run(bad_draft, state.findings)
    assert not critique.approved
    assert critique.unsupported_claims
    state.critique = critique
    state.phase = "critique"
    assert sup.decide_next(state) == "writer_revision"


def test_revision_loop_is_capped():
    sup = make_supervisor(max_revisions=2)
    state = ResearchState(topic="x", phase="critique", revision_count=2)
    from research_team.state import Critique
    state.critique = Critique(approved=False, unsupported_claims=["x"])
    assert sup.decide_next(state) is None


def test_credibility_journal_beats_blog():
    journal = Source(source_id="J", title="t", source_type="journal", year=2024, url="https://x")
    blog = Source(source_id="B", title="t", source_type="blog", year=2022)
    assert score_credibility(journal) > score_credibility(blog)


def test_end_to_end_offline_report_has_citations_and_evidence_table():
    sup = make_supervisor()
    state = sup.run("explainable AI in healthcare", save=False)
    assert state.status == "complete"
    assert len(state.sources) >= 3
    assert state.critique and state.critique.approved
    assert "## Evidence Table" in state.draft
    assert "| Claim | Source | Credibility |" in state.draft
    assert "[S" in state.draft  # citation markers present
    assert "## References" in state.draft
    # Every key-finding bullet is cited
    in_findings = False
    for line in state.draft.splitlines():
        if line.startswith("## Key Findings"):
            in_findings = True
            continue
        if line.startswith("## ") and in_findings:
            break
        if in_findings and line.startswith("- "):
            assert "[" in line and "]" in line, line


def test_second_topic_also_completes():
    sup = make_supervisor()
    state = sup.run("LLM agents and multi-agent systems", save=False)
    assert len(state.sources) >= 3
    assert "## Evidence Table" in state.draft
