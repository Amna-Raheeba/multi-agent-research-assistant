"""Optional LLM adapter.

The pipeline does NOT depend on this. Agents are heuristic and
deterministic offline; if an API key is present and the caller opts in,
this adapter can be used to polish prose. Keeping the LLM at the edge
means tests never flake because a model changed its mind.
"""
from __future__ import annotations

import json
import os
import urllib.request


class LLMAdapter:
    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None):
        self.model = model
        self.api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def generate(self, prompt: str) -> str | None:
        """Return generated text, or None when no key is configured."""
        if not self.available:
            return None
        payload = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }).encode()
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:  # pragma: no cover - network
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]
