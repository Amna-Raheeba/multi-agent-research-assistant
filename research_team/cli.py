"""CLI: python -m research_team "explainable AI in healthcare" """
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import Settings
from .supervisor import Supervisor


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="research_team", description="Multi-agent research assistant (offline by default)")
    parser.add_argument("topic", help="Research topic, in quotes")
    parser.add_argument("--output", "-o", help="Write the report to this Markdown file")
    parser.add_argument("--budget", type=float, help="Estimated budget in USD for this run")
    parser.add_argument("--max-revisions", type=int)
    parser.add_argument("--show-trace", action="store_true", help="Print the per-agent trace")
    parser.add_argument("--show-budget", action="store_true", help="Print per-agent cost estimate")
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    if args.budget is not None:
        settings.budget_usd = args.budget
    if args.max_revisions is not None:
        settings.max_revisions = args.max_revisions

    supervisor = Supervisor(settings)
    state = supervisor.run(args.topic)

    print(state.draft)
    print(f"\n---\nStatus: {state.status} | Sources: {len(state.sources)} | "
          f"Findings: {len(state.findings)} | Revisions: {state.revision_count} | "
          f"Critic approved: {bool(state.critique and state.critique.approved)}")
    if args.show_budget:
        print(json.dumps(supervisor.budget.summary(), indent=2))
    if args.show_trace:
        for e in state.trace:
            print(f"[{e['t_ms']}ms] {e['agent']}: {e['action']} — {e['detail']}")
    if args.output:
        Path(args.output).write_text(state.draft, encoding="utf-8")
        print(f"Report written to {args.output}", file=sys.stderr)
    return 0 if state.status in {"complete", "budget_exceeded", "max_iterations"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
