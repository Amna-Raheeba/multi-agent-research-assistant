"""Configuration loaded from environment, with offline-first defaults.

I kept this deliberately boring: a dataclass, no config framework.
The pipeline should run on a fresh clone with zero env vars set.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent
DEFAULT_FIXTURES = PROJECT_ROOT / "data" / "fixtures.json"
DEFAULT_RUNS_DIR = PROJECT_ROOT / ".runs"

# Rough list prices (USD per 1k tokens) used only for *estimates*.
# These are not billing figures — they exist so the budget guard has
# something realistic to trip on in offline runs.
PRICE_PER_1K = {"input": 0.00015, "output": 0.0006}


@dataclass
class Settings:
    max_iterations: int = 10
    max_revisions: int = 2
    budget_usd: float = 0.25
    max_sources: int = 8
    offline: bool = True
    fixtures_path: Path = field(default_factory=lambda: DEFAULT_FIXTURES)
    runs_dir: Path = field(default_factory=lambda: DEFAULT_RUNS_DIR)
    use_online_search: bool = False
    model_name: str = "offline-heuristic-v1"

    @classmethod
    def from_env(cls) -> "Settings":
        def _bool(name: str, default: bool) -> bool:
            raw = os.getenv(name)
            if raw is None:
                return default
            return raw.strip().lower() in {"1", "true", "yes", "on"}

        return cls(
            max_iterations=int(os.getenv("RESEARCH_TEAM_MAX_ITERATIONS", "10")),
            max_revisions=int(os.getenv("RESEARCH_TEAM_MAX_REVISIONS", "2")),
            budget_usd=float(os.getenv("RESEARCH_TEAM_BUDGET_USD", "0.25")),
            max_sources=int(os.getenv("RESEARCH_TEAM_MAX_SOURCES", "8")),
            offline=_bool("RESEARCH_TEAM_OFFLINE", True),
            use_online_search=_bool("RESEARCH_TEAM_ONLINE_SEARCH", False),
            model_name=os.getenv("RESEARCH_TEAM_MODEL", "offline-heuristic-v1"),
        )


def estimate_tokens(text: str) -> int:
    """Cheap token estimate: ~4 chars/token, min 1 for non-empty text."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1000) * PRICE_PER_1K["input"] + (output_tokens / 1000) * PRICE_PER_1K["output"]
