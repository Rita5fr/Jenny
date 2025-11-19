"""Memory utility functions wrapping Mem0 service."""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.services.memory import (
    add_memory as add_mem0_memory,
    search_memory as search_mem0_memory,
    get_all_memories,
)

logger = logging.getLogger(__name__)


async def add_memory(text: str, user_id: str) -> Dict[str, Any]:
    """
    Persist text as a memory via the official Mem0 service.

    Args:
        text: The text content to store
        user_id: User identifier

    Returns:
        Dictionary with operation results
    """
    messages = [{"role": "user", "content": text}]
    result = await add_mem0_memory(user_id=user_id, messages=messages)

    if result.get("success"):
        return result.get("result", {})
    else:
        logger.error(f"Failed to add memory: {result.get('error')}")
        return {"error": result.get("error")}


async def search_memory(query: str, user_id: str, k: int = 5) -> Dict[str, Any]:
    """
    Search stored memories for the given user.

    Args:
        query: Search query string
        user_id: User identifier
        k: Number of results to return

    Returns:
        Dictionary with search results
    """
    result = await search_mem0_memory(user_id=user_id, query=query, limit=k)

    if result.get("success"):
        return {"results": result.get("results", [])}
    else:
        logger.error(f"Failed to search memory: {result.get('error')}")
        return {"results": []}


async def get_user_context(user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Return a small window of the user's context from Mem0.

    Args:
        user_id: User identifier
        limit: Maximum number of context items to return

    Returns:
        List of user context/memory items
    """
    try:
        result = await get_all_memories(user_id=user_id, limit=limit)
        if result.get("success"):
            return result.get("memories", [])
        return []
    except Exception as exc:
        logger.warning("Failed to retrieve user context for %s: %s", user_id, exc)
        return []


__all__ = [
    "add_memory",
    "search_memory",
    "get_user_context",
]
