"""Basic Neo4j helper functions."""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from neo4j import AsyncDriver, AsyncGraphDatabase
from neo4j.exceptions import Neo4jError

_driver: Optional[AsyncDriver] = None


def _get_credentials() -> tuple[str, str, str]:
    uri = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "test1234")
    return uri, user, password


async def get_driver() -> AsyncDriver:
    """Return a singleton async driver."""

    global _driver  # noqa: PLW0603
    if _driver is None:
        uri, user, password = _get_credentials()
        _driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    return _driver


async def close_driver() -> None:
    """Close the global driver if initialised."""

    global _driver  # noqa: PLW0603
    if _driver is not None:
        await _driver.close()
        _driver = None


async def create_node(label: str, properties: Dict[str, Any]) -> Dict[str, Any]:
    """Create a node with the provided label and properties."""

    driver = await get_driver()
    cypher = f"CREATE (n:{label} $props) RETURN n"
    try:
        async with driver.session() as session:
            result = await session.run(cypher, props=properties)
            record = await result.single()
            return record["n"]._properties if record else {}
    except Neo4jError as exc:  # noqa: BLE001
        raise RuntimeError("Failed to create node") from exc


async def find_nodes(
    label: str,
    match: Dict[str, Any],
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Return nodes matching the provided criteria."""

    driver = await get_driver()
    where_clauses = " AND ".join(f"n.{key} = ${key}" for key in match) or "true"
    cypher = f"MATCH (n:{label}) WHERE {where_clauses} RETURN n LIMIT $limit"
    params = {**match, "limit": limit}

    try:
        async with driver.session() as session:
            result = await session.run(cypher, params)
            records = await result.to_list()
            return [record["n"]._properties for record in records]
    except Neo4jError as exc:  # noqa: BLE001
        raise RuntimeError("Failed to query nodes") from exc


async def delete_nodes(label: str, match: Dict[str, Any]) -> None:
    """Delete nodes matching the provided properties."""

    driver = await get_driver()
    where_clauses = " AND ".join(f"n.{key} = ${key}" for key in match) or "true"
    cypher = f"MATCH (n:{label}) WHERE {where_clauses} DETACH DELETE n"

    try:
        async with driver.session() as session:
            await session.run(cypher, match)
    except Neo4jError as exc:  # noqa: BLE001
        raise RuntimeError("Failed to delete nodes") from exc
