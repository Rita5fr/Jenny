"""CrewAI Crew for Jenny - Multi-agent orchestration with intelligent routing."""
from __future__ import annotations

import logging
from typing import Any, Dict

from crewai import Crew, Task, Process
from crewai.tasks.task_output import TaskOutput

from app.crew.agents import (
    create_memory_agent,
    create_task_agent,
    create_calendar_agent,
    create_profile_agent,
    create_general_agent,
)

logger = logging.getLogger(__name__)


class JennyCrew:
    """
    Jenny's multi-agent crew using CrewAI.

    This replaces the old keyword-based orchestrator with intelligent LLM-based routing.
    """

    def __init__(self):
        """Initialize the crew with all specialized agents."""
        # Create all agents
        self.memory_agent = create_memory_agent()
        self.task_agent = create_task_agent()
        self.calendar_agent = create_calendar_agent()
        self.profile_agent = create_profile_agent()
        self.general_agent = create_general_agent()

        # Store for easy access
        self.agents = {
            "memory": self.memory_agent,
            "task": self.task_agent,
            "calendar": self.calendar_agent,
            "profile": self.profile_agent,
            "general": self.general_agent,
        }

        logger.info("JennyCrew initialized with %d agents", len(self.agents))

    def _create_task(self, query: str, user_id: str, context: Dict[str, Any]) -> Task:
        """
        Create a CrewAI task from user query.

        The task description is crucial - it tells agents what to do.
        """
        # Build context string
        context_str = f"User ID: {user_id}\n"

        if context.get("session"):
            session = context["session"]
            if session.history:
                recent_history = session.history[-3:]  # Last 3 messages
                context_str += "Recent conversation:\n"
                for msg in recent_history:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    context_str += f"  {role}: {content}\n"

        # Create task description with full context
        task_description = f"""
User Query: {query}

Context:
{context_str}

Your task is to understand this query and provide a helpful response.

Guidelines:
1. Analyze what the user is asking for
2. Determine if this requires:
   - Remembering or recalling information (use memory tools)
   - Creating/managing tasks or reminders (use task tools)
   - Managing calendar or scheduling (use calendar tools)
   - Updating user preferences (use memory tools)
   - General conversation or questions (respond directly)

3. Use the appropriate tools to help the user
4. Provide a clear, concise, and friendly response
5. If you need more information, ask clarifying questions

Remember: You are Jenny, a helpful AI assistant. Be friendly, concise, and helpful.
"""

        return Task(
            description=task_description,
            expected_output="A helpful response to the user's query",
            agent=self._select_primary_agent(query),
        )

    def _select_primary_agent(self, query: str) -> Any:
        """
        Intelligently select which agent should handle the query.

        This is a heuristic-based pre-filter to optimize performance.
        The LLM can still delegate if needed.
        """
        query_lower = query.lower()

        # Memory keywords
        if any(kw in query_lower for kw in [
            "remember", "recall", "what did i", "what do i", "you know about",
            "note", "save", "store", "forget", "my preference"
        ]):
            logger.info("Routing to memory_agent based on keywords")
            return self.memory_agent

        # Task keywords
        if any(kw in query_lower for kw in [
            "remind", "reminder", "task", "todo", "to-do", "list",
            "complete", "done", "finish", "delete task"
        ]):
            logger.info("Routing to task_agent based on keywords")
            return self.task_agent

        # Calendar keywords
        if any(kw in query_lower for kw in [
            "calendar", "schedule", "meeting", "appointment", "event",
            "book", "reserve", "what's on my", "whats on my"
        ]):
            logger.info("Routing to calendar_agent based on keywords")
            return self.calendar_agent

        # Profile keywords
        if any(kw in query_lower for kw in [
            "preference", "setting", "profile", "habit", "routine",
            "dietary", "allergy", "favorite", "favourite"
        ]):
            logger.info("Routing to profile_agent based on keywords")
            return self.profile_agent

        # Default to general agent
        logger.info("Routing to general_agent (no specific keywords matched)")
        return self.general_agent

    async def process_query(self, query: str, user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a user query using the crew.

        Args:
            query: User's question or request
            user_id: User identifier
            context: Additional context (session, metadata, etc.)

        Returns:
            Dictionary with agent response
        """
        try:
            logger.info(f"Processing query for user {user_id}: {query}")

            # Create task
            task = self._create_task(query, user_id, context)

            # Create crew with selected agent
            # Using sequential process - single agent handles it
            crew = Crew(
                agents=[task.agent],  # Just the selected agent
                tasks=[task],
                process=Process.sequential,
                verbose=True,
            )

            # Execute the crew
            # Note: CrewAI's kickoff is synchronous, but we can call it from async
            result = crew.kickoff()

            # Extract response
            if isinstance(result, TaskOutput):
                reply = result.raw
            elif isinstance(result, str):
                reply = result
            else:
                reply = str(result)

            logger.info(f"Crew completed. Agent: {task.agent.role}")

            return {
                "agent": task.agent.role,
                "reply": reply,
                "success": True,
            }

        except Exception as exc:
            logger.exception(f"Error processing query: {exc}")
            return {
                "agent": "error",
                "reply": f"I encountered an error: {str(exc)}. Please try again.",
                "success": False,
                "error": str(exc),
            }

    def get_agent_info(self) -> Dict[str, Dict[str, str]]:
        """Get information about all available agents."""
        return {
            name: {
                "role": agent.role,
                "goal": agent.goal,
            }
            for name, agent in self.agents.items()
        }


# ============================================
# Singleton instance
# ============================================

_crew_instance = None


def get_crew() -> JennyCrew:
    """Get the singleton Jenny crew instance."""
    global _crew_instance
    if _crew_instance is None:
        _crew_instance = JennyCrew()
    return _crew_instance


__all__ = ["JennyCrew", "get_crew"]
