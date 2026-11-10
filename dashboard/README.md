# Dashboard

A Streamlit front-end for the research-team pipeline. It runs the
actual supervisor pipeline in the page — nothing is pre-generated —
and shows the artefacts a report normally hides.

## What it shows

- **Run summary** — status, source/finding counts, revision count,
  contradictions flagged, critic verdict, estimated run cost.
- **Report** — the writer's draft exactly as the CLI prints it,
  including the **Conflicting Evidence** section when the evidence
  graph flags a contradiction.
- **Evidence table** — every claim with its source and credibility
  score, as produced by the analyst.
- **Evidence graph** — the claim↔source bipartite graph drawn from the
  run's `evidence_graph` data (sources left, claims right, line
  thickness = credibility), with node/edge counts and the same graph
  as a claim → source mapping table.
- **Contradictions** — each flagged pair side by side, with both
  sources' credibility.
- **Budget by agent** — the BudgetTracker's per-agent token and cost
  estimates, plus how much of the run budget was used.
- **Run trace** — the per-agent event log, in an expander.

## Run it

From the project root:

```bash
pip install streamlit
streamlit run dashboard/app.py
```

Pick one of the three fixture topics in the sidebar, or type a
free-text topic. Search runs over the offline fixture corpus by
default, so a topic outside the corpus's three areas will honestly
come back with few or no sources.

## Layout

```
dashboard/
├── app.py       # the Streamlit app (presentation only)
├── helpers.py   # pure-Python data shaping, no streamlit import —
│                # unit-tested in tests/test_dashboard_helpers.py
└── README.md    # this file
```

Streamlit (and matplotlib, for the graph figure) are dashboard-only
dependencies. The core `research_team` package stays standard-library
only, and neither is added to the project's `requirements.txt`.
