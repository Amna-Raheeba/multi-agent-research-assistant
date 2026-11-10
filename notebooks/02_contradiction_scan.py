"""How much do the fixture sources actually disagree with each other?

Question (8 Nov 2026): the contradiction detector exists, but is it
firing on the real corpus or only on my planted test pair? This scan
runs the full pipeline on every fixture topic, collects whatever the
detector flags, and writes the result to results/contradiction_scan.csv
— one row per flagged pair, empty topics get no rows (which is itself
the finding I want to be able to check later).

Run from the project root:  python notebooks/02_contradiction_scan.py
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research_team.config import Settings  # noqa: E402
from research_team.evaluation.evaluate import FIXTURE_TOPICS  # noqa: E402
from research_team.supervisor import Supervisor  # noqa: E402

RESULTS = Path(__file__).resolve().parents[1] / "results" / "contradiction_scan.csv"
FIELDS = ["topic", "claim_a", "source_a", "claim_b", "source_b", "shared_terms"]


def main() -> None:
    rows = []
    for topic in FIXTURE_TOPICS:
        state = Supervisor(Settings()).run(topic, save=False)
        print(f"{topic}: {len(state.sources)} sources, "
              f"{len(state.contradictions)} contradiction(s)")
        for c in state.contradictions:
            print(f"  [{c['source_a']}] {c['claim_a']}")
            print(f"  [{c['source_b']}] {c['claim_b']}")
            rows.append({
                "topic": topic,
                "claim_a": c["claim_a"],
                "source_a": c["source_a"],
                "claim_b": c["claim_b"],
                "source_b": c["source_b"],
                "shared_terms": "; ".join(c["shared_terms"]),
            })
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {len(rows)} row(s) to {RESULTS}")


if __name__ == "__main__":
    main()
