"""Stub mail agent."""
from __future__ import annotations

from typing import Any, Dict


async def mail_agent(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Return a placeholder mail response."""

    return {
        "message": "Mail agent stub",
        "query": query,
        "context": context,
    }
