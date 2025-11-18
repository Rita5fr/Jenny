"""Mem0 microservice backed by Postgres and pgvector."""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, List, Optional

import numpy as np
import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, status
from openai import OpenAI
from pgvector import Vector
from pgvector.psycopg2 import register_vector
from psycopg2 import sql
from psycopg2.pool import SimpleConnectionPool
from pydantic import BaseModel, Field, ValidationError

from app.core import cache as cache_utils
from app.core import graph

logger = logging.getLogger("mem0")
logging.basicConfig(level=logging.INFO)

ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env", override=False)

DATABASE_SETTINGS = {
    "host": os.getenv("PGHOST", "127.0.0.1"),
    "port": os.getenv("PGPORT", "5432"),
    "dbname": os.getenv("PGDATABASE", "mem0"),
    "user": os.getenv("PGUSER", "jenny"),
    "password": os.getenv("PGPASSWORD", "jenny123"),
    "sslmode": os.getenv("PGSSLMODE", "disable"),
}

EMBEDDING_MODEL = os.getenv("MEMO_EMBED_MODEL", "text-embedding-3-small")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY is not set; falling back to deterministic embeddings.")

pool: Optional[SimpleConnectionPool] = None
openai_client: Optional[OpenAI] = None

VECTOR_DIMENSION = 1536


def _create_pool(retries: int = 5, delay: float = 1.0) -> SimpleConnectionPool:
    logger.info("Initializing Postgres connection pool.")
    last_error: Optional[Exception] = None

    for attempt in range(1, retries + 1):
        try:
            connection_pool = SimpleConnectionPool(minconn=1, maxconn=5, **DATABASE_SETTINGS)
            break
        except psycopg2.Error as exc:  # noqa: BLE001
            last_error = exc
            logger.warning(
                "Postgres unavailable (attempt %s/%s): %s",
                attempt,
                retries,
                exc,
            )
            if attempt < retries:
                time.sleep(delay)
            else:
                logger.exception("Failed to establish Postgres connection pool.")
                raise RuntimeError("Could not connect to Postgres") from exc
    else:  # pragma: no cover
        raise RuntimeError("Could not connect to Postgres") from last_error

    conn = connection_pool.getconn()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS mem0 (
                    id UUID PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    embedding vector(%s),
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                """,
                (VECTOR_DIMENSION,),
            )
        register_vector(conn)
    finally:
        connection_pool.putconn(conn)
    return connection_pool


@contextmanager
def get_connection():
    if pool is None:
        raise RuntimeError("Database pool has not been initialized.")
    conn = pool.getconn()
    try:
        register_vector(conn)
        yield conn
    finally:
        pool.putconn(conn)


def embed_text(text: str) -> List[float]:
    if openai_client:
        try:
            response = openai_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to generate embedding via OpenAI.")
            raise RuntimeError("Embedding service error") from exc

        try:
            return response.data[0].embedding  # type: ignore[no-any-return]
        except (AttributeError, IndexError, ValidationError) as exc:
            raise RuntimeError("Invalid embedding response") from exc

    logger.debug("Using deterministic fallback embedding.")
    rng = np.random.default_rng(abs(hash(text)) % (2**32))
    vector = rng.standard_normal(VECTOR_DIMENSION)
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector.tolist()
    return (vector / norm).tolist()


class Message(BaseModel):
    role: str = Field(..., description="Role of the message author.")
    content: str = Field(..., min_length=1, description="Message content.")


class MemoryRequest(BaseModel):
    messages: List[Message] = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)


class ResetRequest(BaseModel):
    user_id: str = Field(..., min_length=1)


app = FastAPI(title="Mem0", version="0.3.0")


@app.on_event("startup")
async def startup() -> None:
    global pool, openai_client  # noqa: PLW0603
    pool = _create_pool()
    openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

    try:
        await cache_utils.get_client()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis unavailable during startup: %s", exc)

    try:
        await graph.get_driver()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Neo4j unavailable during startup: %s", exc)

    logger.info("Mem0 service initialized.")


@app.on_event("shutdown")
async def shutdown() -> None:
    if pool:
        pool.closeall()
    try:
        await cache_utils.close_client()
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to close Redis client: %s", exc)
    try:
        await graph.close_driver()
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to close Neo4j driver: %s", exc)
    logger.info("Mem0 service shutdown complete.")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/memories")
async def create_memory(payload: MemoryRequest) -> dict[str, Iterable[dict[str, str]]]:
    user_text = " ".join(msg.content.strip() for msg in payload.messages if msg.role == "user")
    if not user_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one user message is required.",
        )

    try:
        embedding = embed_text(user_text)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    record_id = uuid.uuid4()

    record = {
        "id": str(record_id),
        "user_id": payload.user_id,
        "text": user_text,
    }

    try:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO mem0 (id, user_id, text, embedding) VALUES (%s, %s, %s, %s::vector)",
                (str(record_id), payload.user_id, user_text, Vector(embedding)),
            )
            conn.commit()
    except psycopg2.Error as exc:  # noqa: BLE001
        logger.exception("Failed to store memory.")
        if "conn" in locals():
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist memory.",
        ) from exc

    cache_key = f"memory:{payload.user_id}:{record['id']}"
    try:
        await cache_utils.set_value(cache_key, json.dumps(record), ttl=600)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to cache memory %s: %s", record["id"], exc)

    try:
        await graph.create_node(
            "Memory",
            {
                "id": record["id"],
                "user_id": record["user_id"],
                "text": record["text"],
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to sync memory with Neo4j: %s", exc)

    return {"results": [{"id": record["id"], "status": "stored"}]}


@app.get("/memories/search")
async def search_memories(
    q: str = Query(..., min_length=1),
    user_id: str = Query(..., min_length=1),
    k: int = Query(default=5, ge=1, le=50),
) -> dict[str, List[dict[str, object]]]:
    cache_key = f"search:{user_id}:{q.strip().lower()}"
    try:
        cached = await cache_utils.get_value(cache_key)
        if cached:
            return {"results": json.loads(cached)}
    except Exception as exc:  # noqa: BLE001
        logger.debug("Search cache read failed: %s", exc)

    try:
        embedding = embed_text(q)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    query = sql.SQL(
        """
        SELECT id, user_id, text, created_at, embedding <-> %s::vector AS score
        FROM mem0
        WHERE user_id = %s
        ORDER BY embedding <-> %s::vector
        LIMIT %s;
        """
    )

    try:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(query, (Vector(embedding), user_id, Vector(embedding), k))
            rows = cur.fetchall()
    except psycopg2.Error as exc:  # noqa: BLE001
        logger.exception("Failed to run vector search.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Vector search failed.",
        ) from exc

    results = [
        {
            "id": str(row[0]),
            "user_id": row[1],
            "text": row[2],
            "created_at": row[3].isoformat() if row[3] else None,
            "score": float(row[4]),
        }
        for row in rows
    ]
    try:
        await cache_utils.set_value(cache_key, json.dumps(results), ttl=120)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Search cache write failed: %s", exc)

    return {"results": results}


@app.post("/reset")
async def reset_memories(payload: ResetRequest) -> dict[str, str]:
    try:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM mem0 WHERE user_id = %s;", (payload.user_id,))
            conn.commit()
    except psycopg2.Error as exc:  # noqa: BLE001
        logger.exception("Failed to reset memories.")
        if 'conn' in locals():
            conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset memories.",
        ) from exc

    try:
        client = await cache_utils.get_client()
        patterns = [
            f"memory:{payload.user_id}:*",
            f"search:{payload.user_id}:*",
        ]
        for pattern in patterns:
            async for key in client.scan_iter(match=pattern):
                await client.delete(key)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to clear Redis cache for user %s: %s", payload.user_id, exc)

    try:
        await graph.delete_nodes("Memory", {"user_id": payload.user_id})
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to delete Neo4j nodes for user %s: %s", payload.user_id, exc)

    return {"status": "reset"}
