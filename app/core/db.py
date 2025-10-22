"""Async-friendly Postgres helpers built on psycopg2 pools."""
from __future__ import annotations

import asyncio
import os
from typing import Any, Iterable, Optional

import psycopg2
from psycopg2.pool import ThreadedConnectionPool

_pool: Optional[ThreadedConnectionPool] = None


def _get_pool() -> ThreadedConnectionPool:
    if _pool is None:
        raise RuntimeError("Postgres pool has not been initialized")
    return _pool


def init_pool(minconn: int = 1, maxconn: int = 10) -> None:
    """Initialise the global psycopg2 connection pool."""

    global _pool  # noqa: PLW0603
    if _pool is not None:
        return

    db_settings = {
        "host": os.getenv("PGHOST", "127.0.0.1"),
        "port": os.getenv("PGPORT", "5432"),
        "dbname": os.getenv("PGDATABASE", "mem0"),
        "user": os.getenv("PGUSER", "jenny"),
        "password": os.getenv("PGPASSWORD", "jenny123"),
        "sslmode": os.getenv("PGSSLMODE", "disable"),
    }

    try:
        _pool = ThreadedConnectionPool(minconn=minconn, maxconn=maxconn, **db_settings)
    except psycopg2.Error as exc:  # noqa: BLE001
        raise RuntimeError("Failed to initialise Postgres pool") from exc


async def close_pool() -> None:
    """Close all connections in the pool."""

    global _pool  # noqa: PLW0603
    if _pool is not None:
        await asyncio.get_running_loop().run_in_executor(None, _pool.closeall)
        _pool = None


def _run_query(query: str, params: Optional[Iterable[Any]], fetch: Optional[str]) -> Any:
    pool = _get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            result = None
            if fetch == "one":
                result = cursor.fetchone()
            elif fetch == "all":
                result = cursor.fetchall()
            conn.commit()
            return result
    except Exception:  # noqa: BLE001
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


async def execute(query: str, params: Optional[Iterable[Any]] = None) -> None:
    """Execute a statement without returning results."""

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _run_query, query, params, None)


async def fetch_one(query: str, params: Optional[Iterable[Any]] = None) -> Any:
    """Return a single row from the database."""

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _run_query, query, params, "one")


async def fetch_all(query: str, params: Optional[Iterable[Any]] = None) -> list[Any]:
    """Return multiple rows from the database."""

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, _run_query, query, params, "all")
    return list(result or [])
