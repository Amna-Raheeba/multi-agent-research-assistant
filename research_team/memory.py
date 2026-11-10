"""JSON checkpointer / run memory.

Not a vector store, not a database — just one JSON file per run under
.runs/. Enough to resume inspection after a crash and to diff two runs
of the same topic. If this ever needs concurrency, it should be replaced.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from .state import ResearchState


class RunMemory:
    def __init__(self, runs_dir: Path):
        self.runs_dir = Path(runs_dir)

    def _path(self, run_id: str) -> Path:
        return self.runs_dir / f"{run_id}.json"

    @staticmethod
    def make_run_id(topic: str) -> str:
        digest = hashlib.sha256(f"{topic}-{time.time()}".encode()).hexdigest()[:10]
        slug = "".join(c if c.isalnum() else "-" for c in topic.lower())[:40].strip("-")
        return f"{slug}-{digest}"

    def save(self, state: ResearchState, run_id: str) -> Path:
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        path = self._path(run_id)
        payload = {"run_id": run_id, "saved_at": time.time(), "state": state.to_dict()}
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def load(self, run_id: str) -> ResearchState | None:
        path = self._path(run_id)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return ResearchState.from_dict(dict(payload["state"]))

    def list_runs(self) -> list[str]:
        if not self.runs_dir.exists():
            return []
        return sorted(p.stem for p in self.runs_dir.glob("*.json"))
