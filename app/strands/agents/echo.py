"""Agent returning a lightly processed echo."""
from __future__ import annotations

from typing import Any, Dict

from .base import Agent


class EchoAgent(Agent):
    """Echo the prompt as a simple baseline."""

    async def handle(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "agent": self.name,
            "summary": f"Echoing input: {prompt.strip()}",
            "context": context,
        }
