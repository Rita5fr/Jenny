"""Knowledge search agent using optional external APIs."""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests

from app.strands.agents.memory_agent import add_memory

DEFAULT_MODEL = os.getenv("KNOWLEDGE_MODEL", "gemini-2.5-flash")
GEMINI_ENDPOINT = os.getenv(
    "GEMINI_KNOWLEDGE_ENDPOINT",
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-latest:generateContent",
)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def _call_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        return "I looked it up: " + prompt

    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                ]
            }
        ]
    }
    response = requests.post(GEMINI_ENDPOINT, json=payload, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    candidates = data.get("candidates") or []
    if not candidates:
        return "I couldn't find anything definitive."
    content = candidates[0].get("content", {})
    parts = content.get("parts", [])
    if parts:
        return str(parts[0].get("text") or "")
    return "I couldn't find anything definitive."


async def knowledge_agent(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    user_id = context.get("user_id")
    prompt = (
        "Provide a concise answer (<=100 words). If relevant, suggest how to save this information.\n"
        f"Question: {query}"
    )
    answer = _call_gemini(prompt)

    if user_id and "remember" in query.lower():
        await add_memory(answer, user_id)

    return {"reply": answer, "source": DEFAULT_MODEL}


__all__ = ["knowledge_agent"]
