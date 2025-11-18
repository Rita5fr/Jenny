"""Task agent backed by Postgres for reminders and todos."""
from __future__ import annotations

import asyncio
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

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

UPDATE_TIMESTAMP_SQL = """
UPDATE jenny_tasks
SET updated_at = NOW()
WHERE id = %s
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


def _parse_due_date(text: str) -> Optional[datetime]:
    text = text.lower()
    now = datetime.now(timezone.utc)
    if "tomorrow" in text:
        return now + timedelta(days=1)
    if "today" in text or "tonight" in text:
        return now
    if "next week" in text:
        return now + timedelta(days=7)
    if match := re.search(r"(\d{4})-(\d{2})-(\d{2})", text):
        try:
            return datetime(
                int(match.group(1)),
                int(match.group(2)),
                int(match.group(3)),
                tzinfo=timezone.utc,
            )
        except ValueError:
            return None
    return None


def _parse_recurrence(text: str) -> Optional[str]:
    lowered = text.lower()
    if "every day" in lowered or "daily" in lowered:
        return "daily"
    if "every week" in lowered or "weekly" in lowered:
        return "weekly"
    if "every month" in lowered or "monthly" in lowered:
        return "monthly"
    return None


def _detect_command(text: str) -> str:
    lowered = text.lower()
    if any(keyword in lowered for keyword in ("list", "show", "what are my tasks")):
        return "list"
    if any(keyword in lowered for keyword in ("complete", "done", "finished")):
        return "complete"
    if any(keyword in lowered for keyword in ("delete", "remove")):
        return "delete"
    return "create"


def _extract_task_id(text: str) -> Optional[str]:
    match = re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", text, re.IGNORECASE
    )
    if match:
        return match.group(0)
    return None


async def task_agent(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle task creation, listing, completion, and deletion."""

    user_id = context.get("user_id")
    if not user_id:
        raise ValueError("user_id required for task operations")

    session = context.get("session")
    pending = None
    if session:
        pending = session.metadata.get("pending_task")

    command = _detect_command(query)
    if pending and command == "create":
        due_at = _parse_due_date(query)
        if due_at:
            title = pending.get("title", "Reminder")
            details = pending.get("details", title)
            recurrence = _parse_recurrence(details + " " + query)
            task = await create_task(
                user_id,
                title=title,
                details=f"{details} ({query})",
                due_at=due_at,
                recurrence=recurrence,
            )
            session.metadata.pop("pending_task", None)  # type: ignore[union-attr]
            reply = f"Task created: {task['title']} (due {task['due_at']})."
            return {"reply": reply, "task": task}
        return {"reply": "I still need a date or time to schedule that reminder."}

    if command == "list":
        tasks = await list_tasks(user_id)
        if not tasks:
            return {"reply": "You have no pending tasks."}
        lines = [f"- {task['title']} (id: {task['id']})" for task in tasks]
        return {"reply": "Here are your open tasks:\n" + "\n".join(lines), "tasks": tasks}

    if command in {"complete", "delete"}:
        task_id = _extract_task_id(query)
        if not task_id:
            return {"reply": "Please provide the task ID to update."}
        if command == "complete":
            result = await complete_task(task_id, user_id)
            if result:
                return {"reply": f"Marked '{result['title']}' as completed.", "task": result}
            return {"reply": "I could not find that task."}
        deleted = await delete_task(task_id, user_id)
        if deleted:
            return {"reply": "Removed the task."}
        return {"reply": "I could not find that task."}

    # default: creation path
    recurrence = _parse_recurrence(query)
    due_at = _parse_due_date(query)
    title = query.strip().capitalize()
    if session and due_at is None:
        session.metadata["pending_task"] = {"title": title, "details": query}  # type: ignore[union-attr]
        return {"reply": "Sure, when should I remind you?"}
    task = await create_task(user_id, title=title, details=query, due_at=due_at, recurrence=recurrence)
    reply = f"Task created: {task['title']}"
    if due_at:
        reply += f" (due {task['due_at']})."
    else:
        reply += "."
    if recurrence:
        reply += f" It recurs {recurrence}."
    return {"reply": reply, "task": task}


__all__ = [
    "task_agent",
    "create_task",
    "list_tasks",
    "complete_task",
    "delete_task",
]
