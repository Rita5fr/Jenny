"""Profile agent for managing user preferences."""
from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, List, Optional

from app.core import db
from app.strands.agents.memory_agent import add_memory, get_user_context

CREATE_PROFILE_TABLE = """
CREATE TABLE IF NOT EXISTS jenny_profiles (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    label TEXT NOT NULL,
    value TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT jenny_profiles_user_label UNIQUE (user_id, label)
);
"""

UPSERT_PROFILE = """
INSERT INTO jenny_profiles (id, user_id, label, value)
VALUES (%s, %s, %s, %s)
ON CONFLICT (user_id, label) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
RETURNING id
"""

SELECT_PROFILES = """
SELECT label, value FROM jenny_profiles WHERE user_id = %s ORDER BY updated_at DESC LIMIT %s
"""

TABLE_INITIALISED = asyncio.Lock()
TABLE_READY = False


async def _ensure_table() -> None:
    global TABLE_READY  # noqa: PLW0603
    if TABLE_READY:
        return
    async with TABLE_INITIALISED:
        if TABLE_READY:
            return
        await db.execute(CREATE_PROFILE_TABLE)
        TABLE_READY = True


def _parse_label(text: str) -> Optional[str]:
    lowered = text.lower()
    if "drink" in lowered:
        return "drink"
    if "diet" in lowered:
        return "diet"
    if "habit" in lowered:
        return "habit"
    if "music" in lowered:
        return "music"
    return None


async def save_preference(user_id: str, label: str, value: str) -> None:
    await _ensure_table()
    await db.execute(UPSERT_PROFILE, (str(uuid.uuid4()), user_id, label, value))


async def get_preferences(user_id: str, limit: int = 5) -> List[Dict[str, str]]:
    await _ensure_table()
    rows = await db.fetch_all(SELECT_PROFILES, (user_id, limit))
    return [{"label": row[0], "value": row[1]} for row in rows]


async def profile_agent(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    user_id = context.get("user_id")
    if not user_id:
        raise ValueError("user_id required for profile operations")

    lowered = query.lower()
    label = _parse_label(lowered)
    if any(verb in lowered for verb in ("set", "update", "remember", "my")) and label:
        await save_preference(user_id, label, query)
        await add_memory(query, user_id)
        return {"reply": f"Updated your {label} preference."}

    preferences = await get_preferences(user_id)
    if not preferences:
        memories = await get_user_context(user_id)
        if memories:
            lines = [item.get("text") or str(item) for item in memories]
            return {"reply": "Here's what I remember: " + "; ".join(lines), "preferences": []}
        return {"reply": "I don't have profile info yet. Tell me something about yourself!"}

    lines = [f"{item['label'].capitalize()}: {item['value']}" for item in preferences]
    return {"reply": "Your profile: " + "; ".join(lines), "preferences": preferences}


__all__ = ["profile_agent", "save_preference", "get_preferences"]
