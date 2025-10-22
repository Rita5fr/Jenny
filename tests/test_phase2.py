from __future__ import annotations

from typing import Any, Dict, Optional

import pytest
from fastapi.testclient import TestClient

from app import main
from app.strands import conversation as conversation_module


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(main, "init_pool", lambda: None)
    with TestClient(main.app) as test_client:
        yield test_client


def test_voice_message_routes_to_memory(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_transcribe(url: str, language_code: Optional[str] = None) -> str:
        return "Remember that I love tea."

    async def fake_memory_agent(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        assert query == "Remember that I love tea."
        return {"reply": "Saved."}

    monkeypatch.setattr(conversation_module, "transcribe_audio", fake_transcribe)
    monkeypatch.setitem(main.orchestrator._agents, "memory_agent", fake_memory_agent)  # type: ignore[attr-defined]

    response = client.post(
        "/ask",
        json={"user_id": "u1", "voice_url": "https://cdn.example.com/audio.opus"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["agent"] == "memory_agent"
    assert body["reply"] == "Saved."


def test_recall_agent_selected_for_questions(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_recall_agent(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"reply": "You enjoy black coffee."}

    monkeypatch.setitem(main.orchestrator._agents, "recall_agent", fake_recall_agent)  # type: ignore[attr-defined]

    response = client.post(
        "/ask",
        json={"user_id": "u2", "text": "What do I like?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["agent"] == "recall_agent"
    assert payload["reply"] == "You enjoy black coffee."


def test_knowledge_routing(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_knowledge_agent(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"reply": "Black coffee has antioxidants."}

    monkeypatch.setitem(main.orchestrator._agents, "knowledge_agent", fake_knowledge_agent)  # type: ignore[attr-defined]

    response = client.post(
        "/ask",
        json={"user_id": "u3", "text": "What are the benefits of black coffee?"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["agent"] == "knowledge_agent"
    assert "antioxidants" in result["reply"].lower()
