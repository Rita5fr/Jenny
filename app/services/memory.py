"""
Official Mem0 Integration Service

This module provides a unified interface to the official Mem0 AI memory layer,
replacing the custom implementation. It supports:
- Short-term memory (conversation context)
- Long-term memory (user preferences, history)
- Entity memory (facts, relationships)
- Graph memory (Neo4j for complex relationships)

Usage:
    from app.services.memory import get_memory_client, add_memory, search_memory

    # Add a memory
    await add_memory(user_id="user_123", messages=[{"role": "user", "content": "I love coffee"}])

    # Search memories
    results = await search_memory(user_id="user_123", query="what do I like?", limit=5)

    # Get all user memories
    all_memories = await get_all_memories(user_id="user_123")
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Flag to track if Mem0 is available
MEM0_AVAILABLE = False
_mem0_client: Optional[Any] = None

try:
    from mem0 import MemoryClient

    MEM0_AVAILABLE = True
    logger.info("Official Mem0 library loaded successfully")
except ImportError:
    logger.warning(
        "mem0ai library not available. Install with: pip install mem0ai\n"
        "Falling back to custom implementation..."
    )
    MemoryClient = None  # type: ignore


def get_mem0_config() -> Dict[str, Any]:
    """
    Get Mem0 configuration from environment variables.

    Configuration supports:
    - Vector store: pgvector (for storing embeddings)
    - Embedder: OpenAI text-embedding-3-small (for creating embeddings - used when saving memories)
    - LLM: DeepSeek Chat or OpenAI (for reading/retrieving memories and generating responses)
    - Graph store: Neo4j (optional, for complex relationships)

    Returns:
        Configuration dictionary for Mem0 client
    """
    config = {
        "vector_store": {
            "provider": "pgvector",
            "config": {
                "host": os.getenv("PGHOST", "localhost"),
                "port": int(os.getenv("PGPORT", "5432")),
                "database": os.getenv("PGDATABASE", "jenny_db"),
                "user": os.getenv("PGUSER", "jenny"),
                "password": os.getenv("PGPASSWORD", "jenny123"),
            },
        },
        "embedder": {
            "provider": "openai",
            "config": {
                "model": os.getenv("MEM0_EMBED_MODEL", "text-embedding-3-small"),
                "api_key": os.getenv("OPENAI_API_KEY"),
            },
        },
    }

    # LLM configuration for reading/retrieving memories
    # Supports: openai (default), deepseek
    llm_provider = os.getenv("MEM0_LLM_PROVIDER", "deepseek").lower()

    if llm_provider == "deepseek":
        # DeepSeek Chat for memory operations (reading/retrieving)
        config["llm"] = {
            "provider": "openai",  # DeepSeek uses OpenAI-compatible API
            "config": {
                "model": os.getenv("MEM0_LLM_MODEL", "deepseek-chat"),
                "api_key": os.getenv("DEEPSEEK_API_KEY"),
                "base_url": "https://api.deepseek.com/v1",
            },
        }
    else:
        # OpenAI GPT for memory operations (fallback)
        config["llm"] = {
            "provider": "openai",
            "config": {
                "model": os.getenv("MEM0_LLM_MODEL", "gpt-4o-mini"),
                "api_key": os.getenv("OPENAI_API_KEY"),
            },
        }

    # Optional: Add Neo4j graph store if configured
    neo4j_uri = os.getenv("NEO4J_URI")
    if neo4j_uri:
        config["graph_store"] = {
            "provider": "neo4j",
            "config": {
                "url": neo4j_uri,
                "username": os.getenv("NEO4J_USER", "neo4j"),
                "password": os.getenv("NEO4J_PASSWORD", "jenny123"),
            },
        }

    return config


def get_memory_client() -> Any:
    """
    Get or create the Mem0 client singleton.

    Returns:
        Mem0 MemoryClient instance

    Raises:
        RuntimeError: If Mem0 is not available and fallback fails
    """
    global _mem0_client

    if _mem0_client is not None:
        return _mem0_client

    if not MEM0_AVAILABLE:
        # Fallback to custom implementation
        logger.warning("Using fallback memory implementation")
        from app.mem0.client import FallbackMemoryClient

        _mem0_client = FallbackMemoryClient()
        return _mem0_client

    try:
        config = get_mem0_config()
        _mem0_client = MemoryClient(config=config)
        logger.info("Mem0 client initialized successfully")
        return _mem0_client
    except Exception as exc:
        logger.exception("Failed to initialize Mem0 client: %s", exc)
        raise RuntimeError(f"Failed to initialize Mem0 client: {exc}") from exc


async def add_memory(
    user_id: str,
    messages: List[Dict[str, str]],
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Add a new memory for a user.

    Args:
        user_id: Unique identifier for the user
        messages: List of message dicts with 'role' and 'content' keys
        metadata: Optional metadata to attach to the memory

    Returns:
        Dictionary with memory ID and status

    Example:
        await add_memory(
            user_id="user_123",
            messages=[
                {"role": "user", "content": "I love coffee"},
                {"role": "assistant", "content": "Noted! I'll remember that you love coffee"}
            ],
            metadata={"source": "telegram", "timestamp": "2024-01-15T10:00:00Z"}
        )
    """
    try:
        client = get_memory_client()

        # Prepare kwargs
        kwargs = {"messages": messages, "user_id": user_id}
        if metadata:
            kwargs["metadata"] = metadata

        # Add memory
        result = client.add(**kwargs)

        logger.info(f"Memory added for user {user_id}: {result}")
        return {"success": True, "result": result}

    except Exception as exc:
        logger.exception(f"Failed to add memory for user {user_id}: {exc}")
        return {"success": False, "error": str(exc)}


async def search_memory(
    user_id: str,
    query: str,
    limit: int = 5,
    filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Search memories for a user using semantic search.

    Args:
        user_id: Unique identifier for the user
        query: Search query string
        limit: Maximum number of results to return (default: 5)
        filters: Optional filters to apply to the search

    Returns:
        Dictionary with search results

    Example:
        results = await search_memory(
            user_id="user_123",
            query="what do I like?",
            limit=5,
            filters={"source": "telegram"}
        )
    """
    try:
        client = get_memory_client()

        # Prepare kwargs
        kwargs = {"query": query, "user_id": user_id, "limit": limit}
        if filters:
            kwargs["filters"] = filters

        # Search memories
        results = client.search(**kwargs)

        logger.debug(f"Memory search for user {user_id}: {len(results)} results")
        return {"success": True, "results": results}

    except Exception as exc:
        logger.exception(f"Failed to search memories for user {user_id}: {exc}")
        return {"success": False, "error": str(exc), "results": []}


async def get_all_memories(
    user_id: str,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Get all memories for a user.

    Args:
        user_id: Unique identifier for the user
        limit: Optional limit on number of memories to return

    Returns:
        Dictionary with all memories

    Example:
        all_memories = await get_all_memories(user_id="user_123", limit=100)
    """
    try:
        client = get_memory_client()

        # Get all memories
        kwargs = {"user_id": user_id}
        if limit:
            kwargs["limit"] = limit

        memories = client.get_all(**kwargs)

        logger.debug(f"Retrieved {len(memories)} memories for user {user_id}")
        return {"success": True, "memories": memories}

    except Exception as exc:
        logger.exception(f"Failed to get all memories for user {user_id}: {exc}")
        return {"success": False, "error": str(exc), "memories": []}


async def delete_memory(
    memory_id: str,
    user_id: str,
) -> Dict[str, Any]:
    """
    Delete a specific memory.

    Args:
        memory_id: ID of the memory to delete
        user_id: User ID (for validation)

    Returns:
        Dictionary with deletion status

    Example:
        await delete_memory(memory_id="mem_123", user_id="user_123")
    """
    try:
        client = get_memory_client()

        # Delete memory
        client.delete(memory_id=memory_id)

        logger.info(f"Memory {memory_id} deleted for user {user_id}")
        return {"success": True, "deleted": True}

    except Exception as exc:
        logger.exception(f"Failed to delete memory {memory_id}: {exc}")
        return {"success": False, "error": str(exc)}


async def reset_user_memories(user_id: str) -> Dict[str, Any]:
    """
    Reset (delete) all memories for a user.

    Args:
        user_id: Unique identifier for the user

    Returns:
        Dictionary with reset status

    Example:
        await reset_user_memories(user_id="user_123")
    """
    try:
        client = get_memory_client()

        # Reset memories
        client.reset(user_id=user_id)

        logger.info(f"All memories reset for user {user_id}")
        return {"success": True, "reset": True}

    except Exception as exc:
        logger.exception(f"Failed to reset memories for user {user_id}: {exc}")
        return {"success": False, "error": str(exc)}


async def update_memory(
    memory_id: str,
    user_id: str,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Update an existing memory.

    Args:
        memory_id: ID of the memory to update
        user_id: User ID (for validation)
        data: Data to update in the memory

    Returns:
        Dictionary with update status

    Example:
        await update_memory(
            memory_id="mem_123",
            user_id="user_123",
            data={"content": "Updated content", "metadata": {"verified": True}}
        )
    """
    try:
        client = get_memory_client()

        # Update memory
        result = client.update(memory_id=memory_id, data=data)

        logger.info(f"Memory {memory_id} updated for user {user_id}")
        return {"success": True, "result": result}

    except Exception as exc:
        logger.exception(f"Failed to update memory {memory_id}: {exc}")
        return {"success": False, "error": str(exc)}


async def get_memory_history(
    user_id: str,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Get recent memory history for a user (useful for conversation context).

    Args:
        user_id: Unique identifier for the user
        limit: Number of recent memories to retrieve

    Returns:
        Dictionary with recent memories

    Example:
        history = await get_memory_history(user_id="user_123", limit=10)
    """
    try:
        client = get_memory_client()

        # Get history
        history = client.history(user_id=user_id, limit=limit)

        logger.debug(f"Retrieved {len(history)} history items for user {user_id}")
        return {"success": True, "history": history}

    except Exception as exc:
        logger.exception(f"Failed to get memory history for user {user_id}: {exc}")
        return {"success": False, "error": str(exc), "history": []}


def is_mem0_available() -> bool:
    """Check if Mem0 is available."""
    return MEM0_AVAILABLE


__all__ = [
    "get_memory_client",
    "add_memory",
    "search_memory",
    "get_all_memories",
    "delete_memory",
    "reset_user_memories",
    "update_memory",
    "get_memory_history",
    "is_mem0_available",
]
