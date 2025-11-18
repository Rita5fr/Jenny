"""Memory agent using official Mem0 integration."""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

from app.services.memory import (
    add_memory as add_mem0_memory,
    search_memory as search_mem0_memory,
)

logger = logging.getLogger(__name__)

PREFERENCE_TRIGGERS = ("my favorite", "i like", "i love", "i prefer")


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


async def forget_memory(topic: str, user_id: str) -> Dict[str, Any]:
    """
    Record that a previous preference is outdated.

    Args:
        topic: Topic to mark as outdated
        user_id: User identifier

    Returns:
        Dictionary with operation results
    """
    note = f"Update: {topic.strip()} is no longer valid."
    return await add_memory(note, user_id)


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
        # Use the new memory service to get recent context
        from app.services.memory import get_all_memories

        result = await get_all_memories(user_id=user_id, limit=limit)
        if result.get("success"):
            return result.get("memories", [])
        return []
    except Exception as exc:
        logger.warning("Failed to retrieve user context for %s: %s", user_id, exc)
        return []


def _should_overwrite(text: str) -> bool:
    lowered = text.lower()
    return any(trigger in lowered for trigger in PREFERENCE_TRIGGERS)


def _extract_topic(text: str) -> str:
    match = re.search(r"forget(?: about)? (.+)", text, re.IGNORECASE)
    if match:
        return match.group(1)
    return text


async def memory_agent(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Route memory operations based on the query."""

    user_id = context.get("user_id", "anonymous")
    lowered = query.lower().strip()

    if lowered.startswith("search::"):
        clean_query = query.split("search::", 1)[1].strip() or query
        return await search_memory(clean_query, user_id)

    if lowered.startswith(("forget", "remove", "erase")):
        topic = _extract_topic(query)
        await forget_memory(topic, user_id)
        return {"ack": f"I've marked '{topic}' as outdated."}

    if _should_overwrite(lowered):
        await add_memory(query, user_id)
        return {"ack": "Updated your preference."}

    await add_memory(query, user_id)
    return {"ack": "Saved the memory."}


__all__ = [
    "add_memory",
    "search_memory",
    "forget_memory",
    "get_user_context",
    "memory_agent",
]
