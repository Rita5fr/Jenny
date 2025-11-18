"""Stub research agent using a placeholder HTTP request."""
from __future__ import annotations

import asyncio
from typing import Any, Dict

import requests


async def research_agent(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Perform a placeholder HTTP request to example.com."""

    loop = asyncio.get_running_loop()

    def _fetch() -> str:
        response = requests.get("https://example.com", timeout=5)
        response.raise_for_status()
        return response.text[:200]

    try:
        snippet = await loop.run_in_executor(None, _fetch)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Research agent failed: {exc}", "query": query}

    return {
        "message": "Research agent stub",
        "query": query,
        "snippet": snippet,
    }
