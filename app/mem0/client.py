"""
Fallback Memory Client

This module provides a fallback implementation that mimics the official Mem0 API
using the existing custom microservice at http://localhost:8081.

This is used when the official mem0ai library is not available.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

MEMO_BASE_URL = os.getenv("MEMO_BASE_URL", "http://127.0.0.1:8081")


class FallbackMemoryClient:
    """
    Fallback memory client that uses the custom Mem0 microservice.

    This client provides the same interface as the official Mem0 MemoryClient
    but routes requests to the custom microservice running on port 8081.
    """

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the fallback memory client.

        Args:
            base_url: Base URL for the Mem0 microservice (default: http://127.0.0.1:8081)
        """
        self.base_url = base_url or MEMO_BASE_URL
        self.client = httpx.AsyncClient(timeout=30.0)
        logger.info(f"FallbackMemoryClient initialized with base URL: {self.base_url}")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    def add(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Add a new memory.

        Args:
            messages: List of message dictionaries
            user_id: User identifier
            metadata: Optional metadata

        Returns:
            Dictionary with results
        """
        try:
            # Call custom Mem0 microservice
            response = httpx.post(
                f"{self.base_url}/memories",
                json={"messages": messages, "user_id": user_id},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            logger.exception(f"Failed to add memory via fallback client: {exc}")
            raise RuntimeError(f"Failed to add memory: {exc}") from exc

    def search(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search memories.

        Args:
            query: Search query
            user_id: User identifier
            limit: Maximum results
            filters: Optional filters (not supported in fallback)

        Returns:
            List of search results
        """
        try:
            # Call custom Mem0 microservice
            response = httpx.get(
                f"{self.base_url}/memories/search",
                params={"q": query, "user_id": user_id, "k": limit},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except Exception as exc:
            logger.exception(f"Failed to search memories via fallback client: {exc}")
            return []

    def get_all(
        self,
        user_id: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all memories for a user.

        Args:
            user_id: User identifier
            limit: Optional limit (not fully supported in fallback)

        Returns:
            List of memories
        """
        try:
            # Use search with empty query to get all
            response = httpx.get(
                f"{self.base_url}/memories/search",
                params={"q": "", "user_id": user_id, "k": limit or 100},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except Exception as exc:
            logger.exception(f"Failed to get all memories via fallback client: {exc}")
            return []

    def delete(self, memory_id: str) -> bool:
        """
        Delete a memory (not fully supported in fallback).

        Args:
            memory_id: Memory identifier

        Returns:
            True if successful
        """
        logger.warning(
            "delete() is not fully supported in fallback client. "
            "Use reset() to delete all user memories."
        )
        return False

    def reset(self, user_id: str) -> Dict[str, str]:
        """
        Reset all memories for a user.

        Args:
            user_id: User identifier

        Returns:
            Status dictionary
        """
        try:
            # Call custom Mem0 microservice
            response = httpx.post(
                f"{self.base_url}/reset",
                json={"user_id": user_id},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            logger.exception(f"Failed to reset memories via fallback client: {exc}")
            raise RuntimeError(f"Failed to reset memories: {exc}") from exc

    def update(
        self,
        memory_id: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Update a memory (not supported in fallback).

        Args:
            memory_id: Memory identifier
            data: Update data

        Returns:
            Result dictionary
        """
        logger.warning("update() is not supported in fallback client")
        return {"success": False, "error": "Update not supported in fallback mode"}

    def history(
        self,
        user_id: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get memory history (uses get_all in fallback).

        Args:
            user_id: User identifier
            limit: Number of items

        Returns:
            List of memory history
        """
        return self.get_all(user_id=user_id, limit=limit)


__all__ = ["FallbackMemoryClient"]
