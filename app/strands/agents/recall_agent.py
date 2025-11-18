"""Recall agent combining memory and reasoning."""
from __future__ import annotations

import asyncio
import os
from textwrap import dedent
from typing import Any, Dict, List, Optional

import requests

from app.strands.agents.memory_agent import get_user_context, search_memory
from app.strands.agents.task_agent import list_tasks

DEEPSEEK_ENDPOINT = os.getenv("DEEPSEEK_ENDPOINT", "https://api.deepseek.com/v1/chat/completions")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-reasoner")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


def _format_context(memories: List[Dict[str, Any]], tasks: List[Dict[str, Any]]) -> str:
    memory_lines = [f"- {item.get('text') or item}" for item in memories]
    task_lines = [f"- {task['title']} (status: {task['status']})" for task in tasks]
    context_sections = []
    if memory_lines:
        context_sections.append("Memories:\n" + "\n".join(memory_lines))
    if task_lines:
        context_sections.append("Tasks:\n" + "\n".join(task_lines))
    return "\n\n".join(context_sections) if context_sections else "No prior information."


def _call_deepseek(prompt: str) -> str:
    if not DEEPSEEK_API_KEY:
        return "Based on what I know: " + prompt
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": "You are Jenny, a helpful personal assistant."},
            {"role": "user", "content": prompt},
        ],
    }
    response = requests.post(DEEPSEEK_ENDPOINT, json=payload, headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json()
    choices = data.get("choices") or []
    if not choices:
        return "I'm not sure, but I'm ready to help with something else."
    message = choices[0].get("message", {})
    return str(message.get("content") or "")


async def recall_agent(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    user_id = context.get("user_id")
    if not user_id:
        raise ValueError("user_id required for recall")

    memories = await search_memory(query, user_id)
    memory_hits = memories.get("results", []) or memories.get("data", [])
    tasks = await list_tasks(user_id)

    prompt_context = _format_context(memory_hits, tasks)
    prompt = dedent(
        f"""
        User question: {query}

        Use the information below to answer. If you lack data, state that you don't know and invite the user to tell you.

        {prompt_context}
        """
    ).strip()

    loop = asyncio.get_running_loop()
    answer = await loop.run_in_executor(None, _call_deepseek, prompt)

    return {
        "reply": answer.strip() or "I'm still thinking about that.",
        "memories": memory_hits,
        "tasks": tasks,
    }


__all__ = ["recall_agent"]
