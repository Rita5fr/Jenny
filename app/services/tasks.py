"""Task management service backed by PostgreSQL."""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core import db

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS jenny_tasks (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    details TEXT,
    due_at TIMESTAMPTZ,
    recurrence TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
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
        await db.execute(CREATE_TABLE_SQL)
        TABLE_READY = True


async def create_task(
    user_id: str,
    title: str,
    details: Optional[str] = None,
    due_at: Optional[datetime] = None,
    recurrence: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new task for the user."""
    await _ensure_table()
    task_id = uuid.uuid4()
    await db.execute(
        """
        INSERT INTO jenny_tasks (id, user_id, title, details, due_at, recurrence)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (str(task_id), user_id, title, details, due_at, recurrence),
    )
    return {
        "id": str(task_id),
        "title": title,
        "details": details,
        "due_at": due_at.isoformat() if due_at else None,
        "recurrence": recurrence,
    }


async def list_tasks(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """List all pending tasks for the user."""
    await _ensure_table()
    records = await db.fetch_all(
        """
        SELECT id, title, details, due_at, recurrence, status
        FROM jenny_tasks
        WHERE user_id = %s AND status = 'pending'
        ORDER BY due_at NULLS LAST, created_at ASC
        LIMIT %s
        """,
        (user_id, limit),
    )
    results: List[Dict[str, Any]] = []
    for row in records:
        due_at = row[3].isoformat() if row[3] else None
        results.append(
            {
                "id": str(row[0]),
                "title": row[1],
                "details": row[2],
                "due_at": due_at,
                "recurrence": row[4],
                "status": row[5],
            }
        )
    return results


async def complete_task(task_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Mark a task as completed."""
    await _ensure_table()
    record = await db.fetch_one(
        """
        UPDATE jenny_tasks
        SET status = 'completed', updated_at = NOW()
        WHERE id = %s AND user_id = %s
        RETURNING id, title
        """,
        (task_id, user_id),
    )
    return {"id": str(record[0]), "title": record[1]} if record else None


async def delete_task(task_id: str, user_id: str) -> bool:
    """Delete a task."""
    await _ensure_table()
    record = await db.fetch_one(
        """
        DELETE FROM jenny_tasks
        WHERE id = %s AND user_id = %s
        RETURNING id
        """,
        (task_id, user_id),
    )
    return record is not None


__all__ = [
    "create_task",
    "list_tasks",
    "complete_task",
    "delete_task",
]
