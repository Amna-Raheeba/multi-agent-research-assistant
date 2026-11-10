"""Per-agent trace log — deliberately simple.

Every agent call appends one JSON-serialisable event. When a run looks
wrong, the trace is the first thing I read; print-debugging a multi-agent
loop is miserable.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Tracer:
    events: list[dict[str, Any]] = field(default_factory=list)
    _start: float = field(default_factory=time.time)

    def log(self, agent: str, action: str, detail: str = "", **extra: Any) -> dict[str, Any]:
        event = {
            "t_ms": int((time.time() - self._start) * 1000),
            "agent": agent,
            "action": action,
            "detail": detail,
            **extra,
        }
        self.events.append(event)
        return event

    def for_agent(self, agent: str) -> list[dict[str, Any]]:
        return [e for e in self.events if e["agent"] == agent]

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for e in self.events:
            counts[e["agent"]] = counts.get(e["agent"], 0) + 1
        return counts
