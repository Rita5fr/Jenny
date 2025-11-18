from __future__ import annotations

import asyncio
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from app import main


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(main, "init_pool", lambda: None)
    with TestClient(main.app) as test_client:
        yield test_client


def test_memory_store_route(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_memory_agent(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        assert context["user_id"] == "u1"
        return {"ack": "Saved preference."}

    orchestrator = main.orchestrator
    monkeypatch.setitem(orchestrator._agents, "memory_agent", fake_memory_agent)  # type: ignore[attr-defined]

    response = client.post(
        "/ask",
        json={"user_id": "u1", "text": "Remember that I like hiking."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["agent"] == "memory_agent"
    assert payload["reply"] == "Saved preference."


def test_task_routing(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_task_agent(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"reply": "Task created."}

    orchestrator = main.orchestrator
    monkeypatch.setitem(orchestrator._agents, "task_agent", fake_task_agent)  # type: ignore[attr-defined]

    response = client.post(
        "/ask",
        json={"user_id": "u2", "text": "Remind me tomorrow to call John."},
    )
    assert response.status_code == 200
    assert response.json()["agent"] == "task_agent"


def test_general_fallback(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_general_agent(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"message": "Handled."}

    orchestrator = main.orchestrator
    monkeypatch.setitem(orchestrator._agents, "general_agent", fake_general_agent)  # type: ignore[attr-defined]

    response = client.post(
        "/ask",
        json={"user_id": "u3", "text": "Anything else?"},
    )
    assert response.status_code == 200
    assert response.json()["agent"] == "general_agent"
