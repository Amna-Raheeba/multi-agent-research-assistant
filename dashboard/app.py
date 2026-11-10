"""Streamlit dashboard for the multi-agent research assistant.

This is a presentation layer over the real pipeline — the Run button
executes ``research_team.supervisor.Supervisor`` on the chosen topic
and renders whatever comes back: the writer's report, the analyst's
evidence table, the evidence graph, flagged contradictions, the
per-agent budget breakdown, and the run trace. Nothing here is
pre-generated; an off-corpus topic honestly returns an empty-ish
report, because search is the offline fixture corpus by default.

Run from the project root:

    pip install streamlit
    streamlit run dashboard/app.py

Streamlit is a dashboard-only dependency — the core package
(``research_team``) stays standard-library only.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Streamlit puts this script's folder on sys.path, not the project
# root, so `import research_team` needs the root added explicitly.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
DASHBOARD_DIR = Path(__file__).resolve().parent
if str(DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_DIR))

import streamlit as st  # noqa: E402

import helpers  # noqa: E402
from research_team.config import Settings  # noqa: E402
from research_team.supervisor import Supervisor  # noqa: E402

try:
    from research_team.evaluation.evaluate import FIXTURE_TOPICS
except Exception:  # pragma: no cover - fallback if evaluation moves
    FIXTURE_TOPICS = [
        "explainable AI in healthcare",
        "LLM agents and multi-agent systems",
        "explainable predictive maintenance",
    ]


def run_pipeline(topic: str) -> dict:
    """Execute the full supervisor pipeline once and shape the results."""
    supervisor = Supervisor(Settings())
    state = supervisor.run(topic, save=False)
    return {
        "topic": topic,
        "state": state,
        "budget": supervisor.budget.summary(),
    }


st.set_page_config(page_title="Multi-Agent Research Assistant", layout="wide")
st.title("Multi-Agent Research Assistant")
st.caption(
    "Supervisor → researcher → analyst → writer → critic, run live in this "
    "page. Search is the offline fixture corpus (13 hand-written source "
    "summaries over 3 topics) unless online search is enabled in settings, "
    "so a free-text topic outside those areas will find little or nothing — "
    "the report says so rather than inventing sources."
)

with st.sidebar:
    st.header("Run the pipeline")
    chosen = st.selectbox("Fixture topic", FIXTURE_TOPICS)
    free_text = st.text_input(
        "…or a free-text topic",
        placeholder="Overrides the selector when filled in",
    )
    topic = free_text.strip() or chosen
    st.write(f"**Topic:** {topic}")
    if st.button("Run pipeline", type="primary"):
        with st.spinner(f"Running the agent team on “{topic}”…"):
            st.session_state["run"] = run_pipeline(topic)
    st.divider()
    st.markdown(
        "**What you get**\n\n"
        "- the generated report (with a Conflicting Evidence section "
        "when the evidence graph flags one)\n"
        "- the evidence table behind every claim\n"
        "- the claim↔source evidence graph\n"
        "- flagged contradictions, with both sources' credibility\n"
        "- the per-agent cost estimate and the full run trace"
    )

run = st.session_state.get("run")
if run is None:
    st.info("Pick a topic in the sidebar and press **Run pipeline**.")
    st.stop()

state = run["state"]
budget = run["budget"]

# ------------------------------------------------------------- summary
totals = helpers.budget_totals(budget)
cols = st.columns(6)
cols[0].metric("Status", state.status)
cols[1].metric("Sources", len(state.sources))
cols[2].metric("Findings", len(state.findings))
cols[3].metric("Revisions", state.revision_count)
cols[4].metric("Contradictions", len(state.contradictions))
cols[5].metric("Est. cost", f"${totals['spent_usd']:.4f}")
if state.critique is not None:
    st.write(f"Critic approved: **{state.critique.approved}**"
             + (f" · unsupported claims sent back: {len(state.critique.unsupported_claims)}"
                if state.critique.unsupported_claims else ""))

# -------------------------------------------------------------- report
st.header("Report")
if state.draft:
    st.markdown(state.draft)
else:
    st.warning("The pipeline produced no draft for this topic.")

# -------------------------------------------------------- evidence table
st.header("Evidence Table")
ev_rows = helpers.evidence_rows(state.evidence_table)
if ev_rows:
    st.dataframe(ev_rows, use_container_width=True, hide_index=True,
                 column_config={
                     "claim": st.column_config.TextColumn("Claim", width="large"),
                     "source": st.column_config.TextColumn("Source", width="medium"),
                     "credibility": st.column_config.NumberColumn("Credibility", format="%.2f"),
                 })
else:
    st.info("No evidence rows — the search found no sources for this topic.")

# ------------------------------------------------------- evidence graph
st.header("Evidence Graph")
counts = helpers.graph_counts(state.evidence_graph)
gcols = st.columns(4)
gcols[0].metric("Nodes", counts["nodes"])
gcols[1].metric("Claim nodes", counts["claims"])
gcols[2].metric("Source nodes", counts["sources"])
gcols[3].metric("Supports edges", counts["edges"])
fig = helpers.graph_figure(state.evidence_graph)
if fig is not None:
    st.pyplot(fig)
mapping = helpers.claim_source_rows(state.evidence_graph)
if mapping:
    with st.expander("Claim → source mapping (the graph as a table)"):
        st.dataframe(mapping, use_container_width=True, hide_index=True)

# -------------------------------------------------------- contradictions
st.header("Contradictions")
contra_rows = helpers.contradiction_rows(state.contradictions, state.sources)
if not contra_rows:
    st.info("No contradictions flagged for this run. The detector only "
            "fires on opposing-polarity findings from different sources "
            "sharing at least 3 content terms, so paraphrased disagreement "
            "is not caught.")
for i, row in enumerate(contra_rows, start=1):
    with st.container(border=True):
        st.markdown(f"**Pair {i} — shared concept:** {row['concept']}")
        left, right = st.columns(2)
        left.markdown(f"“{row['claim_a']}”\n\n[{row['source_a']}] · "
                      f"credibility {row['credibility_a']:.2f}")
        right.markdown(f"“{row['claim_b']}”\n\n[{row['source_b']}] · "
                       f"credibility {row['credibility_b']:.2f}")

# --------------------------------------------------------------- budget
st.header("Budget by Agent")
st.caption("Estimated tokens and cost per agent, from the supervisor's "
           "BudgetTracker. Estimates use list-price constants — they are "
           "not billed amounts.")
b_rows = helpers.budget_rows(budget)
if b_rows:
    st.dataframe(b_rows, use_container_width=True, hide_index=True,
                 column_config={
                     "cost_usd": st.column_config.NumberColumn("Cost (USD)", format="$%.6f"),
                     "share_pct": st.column_config.NumberColumn("Share", format="%.1f%%"),
                 })
st.write(f"Spent **${totals['spent_usd']:.6f}** of a ${totals['budget_usd']:.2f} "
         f"budget ({totals['used_pct']:.2f}% used, "
         f"${totals['remaining_usd']:.6f} remaining).")

# ---------------------------------------------------------------- trace
with st.expander(f"Run trace ({len(state.trace)} events)"):
    lines = helpers.trace_lines(state.trace)
    if lines:
        st.code("\n".join(lines), language=None)
    else:
        st.write("No trace events recorded.")
