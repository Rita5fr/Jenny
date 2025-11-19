"""CrewAI Crew for Jenny - Multi-agent orchestration following official best practices."""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from langchain_openai import ChatOpenAI

from app.crew.tools import (
    MemorySearchTool,
    MemoryAddTool,
    MemoryContextTool,
    TaskCreateTool,
    TaskListTool,
    TaskCompleteTool,
    TaskDeleteTool,
    CalendarListEventsTool,
    CalendarCreateEventTool,
    CalendarSearchEventsTool,
)

logger = logging.getLogger(__name__)


def get_llm():
    """Get the LLM instance for agents."""
    return ChatOpenAI(
        model="gpt-4o-mini",  # Fast and cost-effective
        temperature=0.7,
    )


@CrewBase
class JennyCrew:
    """
    Jenny's AI Assistant Crew using CrewAI best practices.

    This crew uses Process.hierarchical for intelligent automatic routing.
    A manager agent is automatically created to delegate tasks to specialist agents.
    """

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # ============================================
    # Agent Definitions
    # ============================================

    @agent
    def memory_keeper(self) -> Agent:
        """Agent responsible for managing user memory using Mem0."""
        return Agent(
            config=self.agents_config['memory_keeper'],
            tools=[
                MemorySearchTool(),
                MemoryAddTool(),
                MemoryContextTool(),
            ],
            llm=get_llm(),
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def task_coordinator(self) -> Agent:
        """Agent responsible for managing tasks and reminders."""
        return Agent(
            config=self.agents_config['task_coordinator'],
            tools=[
                TaskCreateTool(),
                TaskListTool(),
                TaskCompleteTool(),
                TaskDeleteTool(),
            ],
            llm=get_llm(),
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def calendar_coordinator(self) -> Agent:
        """Agent responsible for managing calendar events."""
        return Agent(
            config=self.agents_config['calendar_coordinator'],
            tools=[
                CalendarListEventsTool(),
                CalendarCreateEventTool(),
                CalendarSearchEventsTool(),
            ],
            llm=get_llm(),
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def profile_manager(self) -> Agent:
        """Agent responsible for managing user preferences and profile."""
        return Agent(
            config=self.agents_config['profile_manager'],
            tools=[
                MemorySearchTool(),
                MemoryAddTool(),
                MemoryContextTool(),
            ],
            llm=get_llm(),
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def general_assistant(self) -> Agent:
        """
        Primary conversational agent - handles greetings and general conversations.

        This is the MAIN agent that users interact with. It can delegate to
        specialist agents when needed.
        """
        return Agent(
            config=self.agents_config['general_assistant'],
            tools=[
                MemorySearchTool(),
                MemoryContextTool(),
            ],
            llm=get_llm(),
            verbose=True,
            allow_delegation=True,  # Can delegate to specialist agents
        )

    # ============================================
    # Task Definition
    # ============================================

    @task
    def handle_user_query_task(self) -> Task:
        """
        Main task for handling user queries.

        With Process.hierarchical, the manager will delegate this to appropriate agents.
        """
        return Task(
            config=self.tasks_config['handle_user_query'],
            # No agent specified - manager decides!
        )

    # ============================================
    # Crew Definition
    # ============================================

    @crew
    def crew(self) -> Crew:
        """
        Creates Jenny's crew with hierarchical process.

        The hierarchical process automatically:
        - Creates a manager agent
        - Manager analyzes queries using LLM
        - Delegates to appropriate specialist agents
        - No manual routing needed!
        """
        logger.info("Creating Jenny crew with hierarchical process")

        return Crew(
            agents=self.agents,  # Automatically populated by @agent decorators
            tasks=self.tasks,     # Automatically populated by @task decorators
            process=Process.hierarchical,  # ✅ Intelligent automatic routing!
            manager_llm=get_llm(),  # LLM for the manager agent
            verbose=True,
        )


# ============================================
# Helper class for easier integration
# ============================================

class JennyCrewRunner:
    """
    Wrapper class for running Jenny crew with custom inputs.

    This makes it easier to integrate with the existing FastAPI app.
    """

    def __init__(self):
        """Initialize the crew (created once, reused for all queries)."""
        logger.info("Initializing Jenny crew...")
        self._crew_instance = JennyCrew().crew()
        logger.info("Jenny crew initialized successfully")

    async def process_query(self, query: str, user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a user query using the crew.

        Args:
            query: User's question or request
            user_id: User identifier
            context: Additional context (metadata, etc.)

        Returns:
            Dictionary with agent response
        """
        try:
            logger.info(f"Processing query for user {user_id}: {query}")

            # Prepare inputs for the crew
            # CrewAI will use Mem0 tools to get context automatically
            inputs = {
                "query": query,
                "user_id": user_id,
                "context": f"User ID: {user_id}",  # Minimal context - Mem0 handles the rest
            }

            # Execute the crew (synchronous call, but we're in async context)
            # CrewAI's kickoff is synchronous
            result = self._crew_instance.kickoff(inputs=inputs)

            # Extract response from CrewAI result
            if hasattr(result, 'raw'):
                reply = result.raw
            elif isinstance(result, str):
                reply = result
            else:
                reply = str(result)

            logger.info("Crew completed successfully")

            return {
                "agent": "hierarchical_crew",  # Manager delegated
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

    def get_agent_info(self) -> Dict[str, str]:
        """Get information about all available agents."""
        return {
            "memory_keeper": "Manages user memory and context using Mem0",
            "task_coordinator": "Handles tasks, reminders, and todos",
            "calendar_coordinator": "Manages calendar events across providers",
            "profile_manager": "Handles user preferences and profile settings",
            "general_assistant": "Handles general questions and conversations",
            "hierarchical_manager": "Automatically delegates to specialist agents",
        }


# ============================================
# Singleton instance
# ============================================

_crew_runner = None


def get_crew() -> JennyCrewRunner:
    """
    Get the singleton Jenny crew runner instance.

    The crew is created once and reused for all queries.
    """
    global _crew_runner
    if _crew_runner is None:
        _crew_runner = JennyCrewRunner()
    return _crew_runner


__all__ = ["JennyCrew", "JennyCrewRunner", "get_crew"]
