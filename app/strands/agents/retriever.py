"""Agent that queries the Mem0 microservice for related memories."""
from __future__ import annotations

from typing import Any, Dict, List

import httpx

from app.core.config import get_settings

from .base import Agent


class RetrieverAgent(Agent):
    """Fetch light-weight context snippets from Mem0."""

    async def handle(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        settings = get_settings()
        url = f"{settings.mem0_base_url}/search"
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json={"query": prompt})
            response.raise_for_status()
            memories: List[Dict[str, Any]] = response.json().get("results", [])
        return {
            "agent": self.name,
            "memories": memories,
            "context": context,
        }
