"""Stub calendar agent."""
from __future__ import annotations

from typing import Any, Dict


async def calendar_agent(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Return a placeholder calendar response."""

    return {
        "message": "Calendar agent stub",
        "query": query,
        "context": context,
    }
