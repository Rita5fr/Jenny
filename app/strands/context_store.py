"""Session and context management for Jenny."""
from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core import cache


@dataclass
class SessionSnapshot:
    """Lightweight structure capturing session state."""

    history: List[Dict[str, Any]] = field(default_factory=list)
    last_intent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "history": self.history,
            "last_intent": self.last_intent,
            "metadata": self.metadata,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionSnapshot":
        return cls(
            history=list(data.get("history", [])),
            last_intent=data.get("last_intent"),
            metadata=dict(data.get("metadata", {})),
            updated_at=float(data.get("updated_at", time.time())),
        )


class SessionStore:
    """TTL-based session store with optional Redis persistence."""

    def __init__(self, ttl_seconds: int = 1800, max_history: int = 20) -> None:
        self._ttl = ttl_seconds
        self._max_history = max_history
        self._store: Dict[str, SessionSnapshot] = {}
        self._lock = asyncio.Lock()
        self._redis_enabled = bool(os.getenv("REDIS_URL"))

    async def _get_or_create(self, user_id: str) -> SessionSnapshot:
        async with self._lock:
            snapshot = await self._load_from_redis(user_id)
            if snapshot:
                self._store[user_id] = snapshot
                return snapshot

            snapshot = self._store.get(user_id)
            if snapshot and not self._is_expired(snapshot):
                return snapshot

            snapshot = SessionSnapshot()
            self._store[user_id] = snapshot
            return snapshot

    def _is_expired(self, snapshot: SessionSnapshot) -> bool:
        return (time.time() - snapshot.updated_at) > self._ttl

    async def get_context(self, user_id: str) -> SessionSnapshot:
        """Return a snapshot of the current session for the user."""

        snapshot = await self._get_or_create(user_id)
        snapshot.updated_at = time.time()
        await self._save_to_redis(user_id, snapshot)
        return snapshot

    async def update_intent(self, user_id: str, intent: str) -> None:
        snapshot = await self._get_or_create(user_id)
        snapshot.last_intent = intent
        snapshot.updated_at = time.time()
        await self._save_to_redis(user_id, snapshot)

    async def append_history(self, user_id: str, entry: Dict[str, Any]) -> None:
        snapshot = await self._get_or_create(user_id)
        snapshot.history.append(entry)
        if len(snapshot.history) > self._max_history:
            snapshot.history = snapshot.history[-self._max_history :]
        snapshot.updated_at = time.time()
        await self._save_to_redis(user_id, snapshot)

    async def update_metadata(self, user_id: str, **metadata: Any) -> None:
        snapshot = await self._get_or_create(user_id)
        snapshot.metadata.update(metadata)
        snapshot.updated_at = time.time()
        await self._save_to_redis(user_id, snapshot)

    async def clear(self, user_id: str) -> None:
        async with self._lock:
            self._store.pop(user_id, None)
        await self._delete_from_redis(user_id)

    def _redis_key(self, user_id: str) -> str:
        return f"jenny:session:{user_id}"

    async def _load_from_redis(self, user_id: str) -> Optional[SessionSnapshot]:
        if not self._redis_enabled:
            return None
        try:
            client = await cache.get_client()
            raw = await client.get(self._redis_key(user_id))
            if not raw:
                return None
            payload = json.loads(raw)
            snapshot = SessionSnapshot.from_dict(payload)
            if self._is_expired(snapshot):
                await client.delete(self._redis_key(user_id))
                return None
            return snapshot
        except Exception:
            self._redis_enabled = False
            return None

    async def _save_to_redis(self, user_id: str, snapshot: SessionSnapshot) -> None:
        if not self._redis_enabled:
            return
        try:
            client = await cache.get_client()
            await client.set(
                self._redis_key(user_id),
                json.dumps(snapshot.to_dict()),
                ex=self._ttl,
            )
        except Exception:
            self._redis_enabled = False

    async def _delete_from_redis(self, user_id: str) -> None:
        if not self._redis_enabled:
            return
        try:
            client = await cache.get_client()
            await client.delete(self._redis_key(user_id))
        except Exception:
            self._redis_enabled = False


__all__ = ["SessionStore", "SessionSnapshot"]
