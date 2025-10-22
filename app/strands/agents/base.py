"""Base protocol for agents."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(slots=True)
class Agent:
    """Base class for simple async agents."""

    name: str
    description: str

    async def handle(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Respond to a prompt using the ambient context."""

        raise NotImplementedError
