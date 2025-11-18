"""Lightweight orchestrator with intent and context awareness."""
from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, Dict, Optional

import time

logger = logging.getLogger(__name__)

from app.core import graph
from app.strands.agents.calendar_agent import calendar_agent
from app.strands.agents.mail_agent import mail_agent
from app.strands.agents.knowledge_agent import knowledge_agent
from app.strands.agents.memory_agent import (
    get_user_context,
    memory_agent,
    search_memory,
)
from app.strands.agents.profile_agent import profile_agent
from app.strands.agents.recall_agent import recall_agent
from app.strands.agents.research_agent import research_agent
from app.strands.agents.task_agent import task_agent
from app.strands.agents.tools_agent import tools_agent
from app.strands.context_store import SessionStore

AgentCallable = Callable[[str, Dict[str, Any]], Awaitable[Any]]


class Orchestrator:
    """Manage lightweight intent routing for registered agents."""

    INTENT_MAP = {
        "memory_agent": {"remember", "note", "save", "favourite", "favorite"},
        "task_agent": {"remind", "task", "todo", "list", "complete", "delete"},
        "profile_agent": {"profile", "preference", "diet", "habit"},
        "knowledge_agent": {"benefits", "information", "explain", "tell me about", "research"},
        "recall_agent": {"what do i", "what are my", "who am i", "summary"},
        "calendar_agent": {"calendar", "meet"},
        "mail_agent": {"email", "inbox"},
        "research_agent": {"search", "research"},
        "tools_agent": {"use tool", "execute", "run tool", "what tools", "list tools", "file read", "web search"},
    }

    def __init__(self, session_store: Optional[SessionStore] = None) -> None:
        self._agents: Dict[str, AgentCallable] = {}
        self._sessions = session_store or SessionStore()
        self.register_agent("memory_agent", memory_agent)
        self.register_agent("calendar_agent", calendar_agent)
        self.register_agent("mail_agent", mail_agent)
        self.register_agent("research_agent", research_agent)
        self.register_agent("task_agent", task_agent)
        self.register_agent("profile_agent", profile_agent)
        self.register_agent("recall_agent", recall_agent)
        self.register_agent("knowledge_agent", knowledge_agent)
        self.register_agent("tools_agent", tools_agent)
        self.register_agent("general_agent", self._general_agent)

    def register_agent(self, name: str, func: AgentCallable) -> None:
        """Register an async callable agent."""

        self._agents[name] = func

    async def invoke(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Route the query to the best-fit agent."""

        if not query.strip():
            raise ValueError("Query must be non-empty")

        user_id = context.get("user_id")
        if user_id:
            session = await self._sessions.get_context(user_id)
            context["session"] = session

        intent = self._detect_intent(query.lower(), context)
        agent = self._agents.get(intent)
        if agent is None:
            raise ValueError(f"No agent registered for intent {intent}")

        response = await agent(query, context)
        reply = self._response_to_text(response)
        if user_id:
            await self._sessions.update_intent(user_id, intent)
            await self._log_interaction(user_id, query, intent, reply)
        return {"agent": intent, "response": response, "reply": reply}

    def _detect_intent(self, query: str, context: Dict[str, Any]) -> str:
        session = context.get("session")
        if session and session.metadata.get("pending_task"):
            return "task_agent"

        for agent, keywords in self.INTENT_MAP.items():
            if any(keyword in query for keyword in keywords):
                return agent
        return "general_agent"

    async def _general_agent(self, query: str, context: Dict[str, Any]) -> Any:
        user_id = context.get("user_id")
        memory_context = None
        if user_id:
            try:
                memory_context = await search_memory(query, user_id)
                if not memory_context.get("results"):
                    memory_context["results"] = await get_user_context(user_id)
                if not memory_context.get("results"):
                    knowledge = await knowledge_agent(query, context)
                    return {
                        "message": knowledge.get("reply"),
                        "knowledge": knowledge,
                    }
            except Exception as exc:
                logger.exception("Error retrieving memory context for user %s: %s", user_id, exc)
                memory_context = None
        return {
            "message": "Handled by general agent",
            "memory_context": memory_context,
        }

    @property
    def session_store(self) -> SessionStore:
        return self._sessions

    @staticmethod
    def _response_to_text(response: Any) -> str:
        if isinstance(response, dict):
            for key in ("reply", "message", "ack"):
                if key in response:
                    return str(response[key])
        return str(response)

    async def _log_interaction(
        self, user_id: str, query: str, agent: str, reply: str
    ) -> None:
        properties = {
            "user_id": user_id,
            "agent": agent,
            "query": query,
            "reply": reply,
            "timestamp": time.time(),
        }
        try:
            await graph.create_node("Interaction", properties)
        except Exception as exc:
            # Logging should never interrupt the main flow.
            logger.warning("Failed to log interaction to Neo4j for user %s: %s", user_id, exc)


__all__ = ["Orchestrator"]
