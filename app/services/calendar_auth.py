"""Calendar OAuth token management service."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core import db

logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS calendar_tokens (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expiry TIMESTAMPTZ,
    token_data JSONB,
    connected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, provider)
);
"""

TABLE_INITIALISED = asyncio.Lock()
TABLE_READY = False


async def _ensure_table() -> None:
    """Ensure calendar_tokens table exists."""
    global TABLE_READY  # noqa: PLW0603
    if TABLE_READY:
        return
    async with TABLE_INITIALISED:
        if TABLE_READY:
            return
        await db.execute(CREATE_TABLE_SQL)
        TABLE_READY = True


async def save_calendar_token(
    user_id: str,
    provider: str,
    access_token: str,
    refresh_token: Optional[str] = None,
    token_expiry: Optional[datetime] = None,
    token_data: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Save or update calendar OAuth token for a user.

    Args:
        user_id: User identifier
        provider: Calendar provider (google, microsoft, apple)
        access_token: OAuth access token
        refresh_token: OAuth refresh token (optional)
        token_expiry: Token expiration datetime (optional)
        token_data: Additional token data as JSON (optional)

    Returns:
        True if successful
    """
    await _ensure_table()

    try:
        await db.execute(
            """
            INSERT INTO calendar_tokens
            (user_id, provider, access_token, refresh_token, token_expiry, token_data)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, provider)
            DO UPDATE SET
                access_token = EXCLUDED.access_token,
                refresh_token = EXCLUDED.refresh_token,
                token_expiry = EXCLUDED.token_expiry,
                token_data = EXCLUDED.token_data,
                updated_at = NOW()
            """,
            (
                user_id,
                provider,
                access_token,
                refresh_token,
                token_expiry,
                json.dumps(token_data) if token_data else None,
            ),
        )
        logger.info(f"Saved {provider} token for user {user_id}")
        return True
    except Exception as exc:
        logger.exception(f"Failed to save calendar token: {exc}")
        return False


async def get_calendar_token(user_id: str, provider: str) -> Optional[Dict[str, Any]]:
    """
    Get calendar OAuth token for a user.

    Args:
        user_id: User identifier
        provider: Calendar provider (google, microsoft, apple)

    Returns:
        Token data dictionary or None if not found
    """
    await _ensure_table()

    try:
        record = await db.fetch_one(
            """
            SELECT access_token, refresh_token, token_expiry, token_data, connected_at
            FROM calendar_tokens
            WHERE user_id = %s AND provider = %s
            """,
            (user_id, provider),
        )

        if not record:
            return None

        token_data_json = record[3]
        token_data = json.loads(token_data_json) if token_data_json else {}

        return {
            "access_token": record[0],
            "refresh_token": record[1],
            "token_expiry": record[2].isoformat() if record[2] else None,
            "token_data": token_data,
            "connected_at": record[4].isoformat() if record[4] else None,
            "provider": provider,
        }
    except Exception as exc:
        logger.exception(f"Failed to get calendar token: {exc}")
        return None


async def delete_calendar_token(user_id: str, provider: str) -> bool:
    """
    Delete calendar OAuth token (disconnect calendar).

    Args:
        user_id: User identifier
        provider: Calendar provider (google, microsoft, apple)

    Returns:
        True if successful
    """
    await _ensure_table()

    try:
        record = await db.fetch_one(
            """
            DELETE FROM calendar_tokens
            WHERE user_id = %s AND provider = %s
            RETURNING id
            """,
            (user_id, provider),
        )

        if record:
            logger.info(f"Disconnected {provider} calendar for user {user_id}")
            return True
        return False
    except Exception as exc:
        logger.exception(f"Failed to delete calendar token: {exc}")
        return False


async def list_connected_calendars(user_id: str) -> List[Dict[str, Any]]:
    """
    List all connected calendar providers for a user.

    Args:
        user_id: User identifier

    Returns:
        List of connected calendar info
    """
    await _ensure_table()

    try:
        records = await db.fetch_all(
            """
            SELECT provider, connected_at, updated_at
            FROM calendar_tokens
            WHERE user_id = %s
            ORDER BY connected_at DESC
            """,
            (user_id,),
        )

        return [
            {
                "provider": record[0],
                "connected_at": record[1].isoformat() if record[1] else None,
                "updated_at": record[2].isoformat() if record[2] else None,
            }
            for record in records
        ]
    except Exception as exc:
        logger.exception(f"Failed to list connected calendars: {exc}")
        return []


async def is_calendar_connected(user_id: str, provider: str) -> bool:
    """
    Check if a calendar provider is connected for a user.

    Args:
        user_id: User identifier
        provider: Calendar provider (google, microsoft, apple)

    Returns:
        True if connected
    """
    token = await get_calendar_token(user_id, provider)
    return token is not None


__all__ = [
    "save_calendar_token",
    "get_calendar_token",
    "delete_calendar_token",
    "list_connected_calendars",
    "is_calendar_connected",
]
