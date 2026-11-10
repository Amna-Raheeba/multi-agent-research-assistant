# Multi-Agent Research Assistant

> A supervisor-orchestrated team of four agents that turns a research topic into a structured, cited report with an evidence table — with hard limits on loops and budget.

**Author:** Amna Raheeba · Plain Python, runs fully offline with no API keys

---

## 1. Overview

### 1.1 The problem
Ask one LLM call to "research X and write a report" and you get fluent text with citations that may not support — or even contain — the claims attached to them. Splitting the work into agents only helps if something checks the joins between them.

### 1.2 The idea
A **supervisor** owns the flow, a **critic** can send a draft back for revision, and both operate under explicit limits: max iterations, max revisions, and a per-agent cost budget. That checking layer is what this project is about; the agents themselves are intentionally simple.

## 2. How It Works

### 2.1 Architecture

```mermaid
flowchart TD
    U[Topic] --> S{Supervisor: routing · loop guard · budget}
    S -->|research| R[Researcher]
    S -->|analysis| A[Analyst]
    S -->|writing| W[Writer]
    S -->|review| C[Critic]
    C --> S
    S -->|unsupported & revisions < 2| W
    S -->|approved / limits hit| OUT[Report + evidence table + trace]
```

### 2.2 The agents

| Agent | Responsibility |
|---|---|
| **Researcher** | Collects sources with search tools; deduplicates; makes no claims of its own |
| **Analyst** | Extracts findings into an evidence table; scores source credibility (journal 0.90 → blog 0.30, with an age penalty) |
| **Writer** | Drafts the structured report from the evidence table only, with `[S#]` citations |
| **Critic** | Mechanically checks: every key finding is cited, and every cited claim exists in the evidence table |

### 2.3 Key concepts

- **Supervisor, not a chain** — the flow is conditional: after review, the run either finishes or loops back to the writer, decided from runtime state. The supervisor is an explicit state machine, not an LLM router — for four agents with a known flow, an LLM router would add cost and non-determinism, not capability.
- **Loops get hard limits** — max iterations (10) and max revisions (2) are enforced in one routing function, `decide_next()`.
- **Budget per agent** — `BudgetTracker` estimates tokens and cost per agent and stops the run over budget, so a revision loop shows exactly which agent is spending.
- **Revision by re-rendering** — the writer revises by re-rendering from the evidence table, so unsupported sentences drop by construction rather than by editing.
- **Offline first** — default search runs over a small hand-written fixture corpus (12 original summaries, 3 topics). DuckDuckGo and arXiv tools are optional and fail soft.

## 3. Quick Start

```bash
# Python 3.10+, no dependencies for the demo
python -m research_team "explainable AI in healthcare"
python -m research_team "LLM agents and multi-agent systems" --show-budget --show-trace
python -m research_team "explainable predictive maintenance" -o report.md

pip install pytest && pytest -q                  # 10 tests
python -m research_team.evaluation.evaluate      # fixture evaluation
```

A full generated report is in [`examples/sample_report.md`](examples/sample_report.md) — 5 sources, 15 findings, critic-approved, estimated run cost ≈ $0.001. Runs are checkpointed as JSON under `.runs/` and can be reloaded for inspection.

## 4. Project Structure

```
research_team/
├── supervisor.py        # routing (decide_next) · loop guard · BudgetTracker
├── state.py             # shared ResearchState / Source / Finding / Critique
├── config.py / memory.py / observability.py   # settings · JSON checkpointer · trace
├── agents/              # researcher · analyst · writer · critic
├── tools/               # fixture search (+ optional DuckDuckGo) · arXiv API
└── evaluation/          # completeness / citation / evidence coverage
data/fixtures.json       # 12 original source summaries across 3 topics
tests/                   # routing · budget guard · critic / revision · end-to-end
```

## 5. Design Decisions

| Decision | Why |
|---|---|
| Mechanical critic, not an LLM judge | The two checks (citation present, claim exists in evidence) are deterministic and unit-testable — and catch the most common failure: claims that were never in any source. |
| Shared state, no hidden agent memory | One dataclass every agent reads/writes; a run can be debugged from a single checkpoint file. |
| Credibility score labelled as a heuristic | It stops a blog post and a journal paper counting equally, without pretending to judge individual papers. |

## 6. Evaluation

On the 3 fixture topics: **section completeness 1.00 · citation coverage 1.00 · evidence coverage 1.00** (5 / 4 / 4 sources, 15 / 12 / 12 findings).

> Honest context: this is a 12-source hand-written corpus where the analyst generates the findings, so high coverage is expected. It is a regression check on the pipeline's plumbing — not evidence the system would score similarly on real literature.

## 7. Limitations & Roadmap

**Limitations:** fixture search is keyword + a small concept map, so it misses paraphrases an embedding search would catch · agents read short summaries, not full texts · the critic checks claim *presence*, not semantic equivalence · cost figures are estimates, not billed amounts · agents run sequentially.

**Roadmap:** embedding retrieval behind the same tool interface · semantic (entailment) critic check · human-rated evaluation on unseen topics against a single-call baseline · parallel researcher calls for online search.

## License

MIT © 2026 Amna Raheeba — see [LICENSE](LICENSE).
