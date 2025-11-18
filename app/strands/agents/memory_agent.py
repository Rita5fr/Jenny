"""Memory agent that talks to the Mem0 microservice."""
from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)

MEMO_BASE_URL = os.getenv("MEMO_BASE_URL", "http://127.0.0.1:8081")
PREFERENCE_TRIGGERS = ("my favorite", "i like", "i love", "i prefer")


async def add_memory(text: str, user_id: str) -> Dict[str, Any]:
    """Persist text as a memory via the Mem0 API."""

    payload = {"messages": [{"role": "user", "content": text}], "user_id": user_id}
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(f"{MEMO_BASE_URL}/memories", json=payload)
        response.raise_for_status()
        return response.json()


async def search_memory(query: str, user_id: str, k: int = 5) -> Dict[str, Any]:
    """Search stored memories for the given user."""

    params = {"q": query, "user_id": user_id, "k": k}
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(f"{MEMO_BASE_URL}/memories/search", params=params)
        response.raise_for_status()
        return response.json()


async def forget_memory(topic: str, user_id: str) -> Dict[str, Any]:
    """Record that a previous preference is outdated."""

    note = f"Update: {topic.strip()} is no longer valid."
    return await add_memory(note, user_id)


async def get_user_context(user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Return a small window of the user's context from Mem0."""

    try:
        # Use a broad query to fetch the latest entries.
        response = await search_memory("*", user_id, k=limit)
        return response.get("results", []) or response.get("data", [])
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
