"""Supervisor: routing, loop guard, and budget accounting.

The supervisor is plain Python, not an LLM. Routing an LLM call for
'what next' after every step costs money and makes failures hard to
reproduce; the state machine here is small enough to be explicit.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .agents.analyst import AnalystAgent
from .agents.critic import CriticAgent
from .agents.researcher import ResearcherAgent
from .agents.writer import WriterAgent
from .config import Settings, estimate_cost, estimate_tokens
from .evidence_graph import analyse_evidence
from .memory import RunMemory
from .observability import Tracer
from .state import ResearchState
from .tools.search_tools import FixtureSearch


@dataclass
class BudgetTracker:
    budget_usd: float
    spent_usd: float = 0.0
    by_agent: dict[str, dict] = field(default_factory=dict)

    def record(self, agent: str, input_text: str, output_text: str) -> float:
        in_tok, out_tok = estimate_tokens(input_text), estimate_tokens(output_text)
        cost = estimate_cost(in_tok, out_tok)
        self.spent_usd += cost
        entry = self.by_agent.setdefault(agent, {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "calls": 0})
        entry["input_tokens"] += in_tok
        entry["output_tokens"] += out_tok
        entry["cost_usd"] = round(entry["cost_usd"] + cost, 6)
        entry["calls"] += 1
        return cost

    @property
    def exceeded(self) -> bool:
        return self.spent_usd > self.budget_usd

    def summary(self) -> dict:
        return {"budget_usd": self.budget_usd, "spent_usd": round(self.spent_usd, 6), "by_agent": self.by_agent}


class Supervisor:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings.from_env()
        self.budget = BudgetTracker(budget_usd=self.settings.budget_usd)
        self.tracer = Tracer()
        self.memory = RunMemory(self.settings.runs_dir)
        search = FixtureSearch(self.settings.fixtures_path)
        self.researcher = ResearcherAgent(search, use_online=self.settings.use_online_search)
        self.analyst = AnalystAgent()
        self.writer = WriterAgent()
        self.critic = CriticAgent()

    # -- routing ---------------------------------------------------------
    def decide_next(self, state: ResearchState) -> str | None:
        """Return the next agent name, or None when the run should stop."""
        if state.iteration >= self.settings.max_iterations:
            return None
        if self.budget.exceeded:
            return None
        if state.phase == "init":
            return "researcher"
        if state.phase == "research":
            return "analyst"
        if state.phase == "analysis":
            return "writer"
        if state.phase == "writing":
            return "critic"
        if state.phase == "critique":
            if state.critique and not state.critique.approved:
                if state.revision_count < self.settings.max_revisions:
                    return "writer_revision"
                return None
            return None
        if state.phase == "revision":
            return "critic"
        return None

    # -- main loop -------------------------------------------------------
    def run(self, topic: str, save: bool = True) -> ResearchState:
        state = ResearchState(topic=topic)
        while True:
            nxt = self.decide_next(state)
            if nxt is None:
                break
            state.iteration += 1
            if state.iteration > self.settings.max_iterations:
                state.status = "max_iterations"
                self.tracer.log("supervisor", "stop", "max iterations reached")
                break
            if self.budget.exceeded:
                state.status = "budget_exceeded"
                self.tracer.log("supervisor", "stop", "budget exceeded", spent=self.budget.spent_usd)
                break
            self.tracer.log("supervisor", "route", f"-> {nxt}", iteration=state.iteration)
            self._step(state, nxt)
            if self.budget.exceeded and state.status == "running":
                state.status = "budget_exceeded"
                break

        if state.status == "running":
            state.status = "complete" if (state.critique and state.critique.approved) else "complete"
            state.phase = "done"
        state.trace = self.tracer.events
        if save:
            run_id = self.memory.make_run_id(topic)
            self.memory.save(state, run_id)
            self.tracer.log("supervisor", "checkpoint", run_id)
            state.trace = self.tracer.events
        return state

    def _step(self, state: ResearchState, nxt: str) -> None:
        s = self.settings
        if nxt == "researcher":
            sources = self.researcher.run(state.topic, max_sources=s.max_sources)
            self.budget.record("researcher", state.topic, " ".join(x.title + x.summary for x in sources))
            state.sources = sources
            state.phase = "research"
            self.tracer.log("researcher", "search", f"{len(sources)} sources", sources=[x.source_id for x in sources])
        elif nxt == "analyst":
            findings, evidence = self.analyst.run(state.sources)
            self.budget.record("analyst", " ".join(x.summary for x in state.sources), " ".join(f.claim for f in findings))
            state.findings, state.evidence_table = findings, evidence
            # Build the evidence graph here, while claims and sources
            # are both in hand: the writer needs the contradiction
            # flags for its Conflicting Evidence section, and the
            # critic needs them for its critique.
            state.evidence_graph, state.contradictions = analyse_evidence(
                evidence, findings, state.sources)
            state.phase = "analysis"
            self.tracer.log("analyst", "extract", f"{len(findings)} findings")
            self.tracer.log("analyst", "evidence_graph",
                            f"{len(state.evidence_graph['nodes'])} nodes, "
                            f"{len(state.evidence_graph['edges'])} edges, "
                            f"{len(state.contradictions)} contradiction(s)")
        elif nxt == "writer":
            draft = self.writer.run(state.topic, state.findings, state.sources,
                                    state.evidence_table, state.contradictions)
            self.budget.record("writer", " ".join(f.claim for f in state.findings), draft)
            state.draft = draft
            state.phase = "writing"
            self.tracer.log("writer", "draft", f"{len(draft)} chars")
        elif nxt == "writer_revision":
            state.revision_count += 1
            unsupported = state.critique.unsupported_claims if state.critique else []
            draft = self.writer.revise(state.topic, state.findings, state.sources,
                                       state.evidence_table, unsupported,
                                       state.contradictions)
            self.budget.record("writer", "revision", draft)
            state.draft = draft
            state.phase = "revision"
            self.tracer.log("writer", "revision", f"revision {state.revision_count}", unsupported=len(unsupported))
        elif nxt == "critic":
            critique = self.critic.run(state.draft, state.findings, state.contradictions)
            self.budget.record("critic", state.draft, " ".join(critique.comments))
            state.critique = critique
            state.phase = "critique"
            self.tracer.log("critic", "review", f"approved={critique.approved}", unsupported=len(critique.unsupported_claims))
