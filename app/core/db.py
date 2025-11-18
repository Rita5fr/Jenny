"""Async-friendly Postgres helpers built on psycopg2 pools."""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Iterable, Optional

import psycopg2
from psycopg2.pool import ThreadedConnectionPool

logger = logging.getLogger(__name__)

_pool: Optional[ThreadedConnectionPool] = None
_pool_enabled: bool = True


def _get_pool() -> Optional[ThreadedConnectionPool]:
    if not _pool_enabled:
        raise RuntimeError("Postgres pool is disabled due to connection failure")
    if _pool is None:
        raise RuntimeError("Postgres pool has not been initialized")
    return _pool


def init_pool(minconn: int = 1, maxconn: int = 10) -> None:
    """Initialise the global psycopg2 connection pool."""

    global _pool, _pool_enabled  # noqa: PLW0603
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
        logger.info("Postgres pool initialized successfully")
    except psycopg2.Error as exc:
        logger.warning("Failed to initialize Postgres pool: %s. Database features will be disabled.", exc)
        _pool_enabled = False


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
