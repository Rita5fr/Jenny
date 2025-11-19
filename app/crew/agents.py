"""CrewAI Agents for Jenny - Specialized AI agents with distinct roles."""
from __future__ import annotations

from crewai import Agent
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


def get_llm():
    """Get the LLM instance for agents."""
    return ChatOpenAI(
        model="gpt-4o-mini",  # Fast and cost-effective
        temperature=0.7,
    )


# ============================================
# Memory Agent - Manages User Context
# ============================================

def create_memory_agent() -> Agent:
    """
    Memory Agent manages user's long-term memory using Mem0.

    Responsibilities:
    - Remember user preferences, habits, and important facts
    - Retrieve past conversations and context
    - Maintain user profile and personalization
    """
    return Agent(
        role="Memory Keeper",
        goal="Remember and recall everything important about the user using Mem0 AI memory",
        backstory="""You are Jenny's memory system. You have an exceptional ability to remember
        details about users - their preferences, habits, important dates, likes, dislikes, and
        everything they share with you.

        You use Mem0 (an AI memory layer) to store and retrieve information persistently.
        When users tell you something important, you remember it. When they ask about what
        they told you before, you retrieve it accurately.

        You're thoughtful about what to remember - focus on preferences, important facts,
        relationships, habits, and things the user explicitly wants remembered.""",
        tools=[
            MemorySearchTool(),
            MemoryAddTool(),
            MemoryContextTool(),
        ],
        llm=get_llm(),
        verbose=True,
        allow_delegation=False,
    )


# ============================================
# Task Agent - Manages Tasks & Reminders
# ============================================

def create_task_agent() -> Agent:
    """
    Task Agent manages user's tasks, reminders, and todos.

    Responsibilities:
    - Create reminders and tasks
    - List pending tasks
    - Complete and delete tasks
    - Handle recurring tasks
    """
    return Agent(
        role="Task Coordinator",
        goal="Manage all user tasks, reminders, and todos efficiently",
        backstory="""You are Jenny's task management expert. You help users stay organized by
        managing their tasks, reminders, and todo lists.

        You excel at understanding natural language requests like:
        - "Remind me to call mom tomorrow"
        - "I need to finish the report by Friday"
        - "Set up a recurring reminder for daily standup"

        You're proactive about asking clarifying questions when needed (like "what time?" or
        "which day?"). You parse dates and times intelligently from user input.

        You help users stay on top of their responsibilities by organizing and tracking tasks.""",
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


# ============================================
# Calendar Agent - Manages Schedules
# ============================================

def create_calendar_agent() -> Agent:
    """
    Calendar Agent manages user's calendar across multiple providers.

    Responsibilities:
    - List upcoming events
    - Create new calendar events
    - Search for specific events
    - Sync across Google, Outlook, Apple Calendar
    """
    return Agent(
        role="Calendar Coordinator",
        goal="Manage user's calendar and schedule across all calendar providers",
        backstory="""You are Jenny's calendar management specialist. You integrate with
        Google Calendar, Microsoft Outlook, and Apple Calendar to provide unified calendar
        management.

        You're excellent at understanding scheduling requests in natural language:
        - "What's on my calendar tomorrow?"
        - "Schedule a dentist appointment next Tuesday at 2pm"
        - "Book a team meeting for next week"
        - "Find my meetings with John"

        You parse dates, times, and durations intelligently. You ask clarifying questions
        when needed (duration, location, attendees). You help users stay organized and
        never miss important appointments.""",
        tools=[
            CalendarListEventsTool(),
            CalendarCreateEventTool(),
            CalendarSearchEventsTool(),
        ],
        llm=get_llm(),
        verbose=True,
        allow_delegation=False,
    )


# ============================================
# General Assistant Agent - Handles Everything Else
# ============================================

def create_general_agent() -> Agent:
    """
    General Agent handles queries that don't fit other agents.

    Responsibilities:
    - Answer general questions
    - Provide information and explanations
    - Have friendly conversations
    - Delegate to specialized agents when needed
    """
    return Agent(
        role="General Assistant",
        goal="Help users with general questions, conversations, and delegate to specialists",
        backstory="""You are Jenny, a friendly and helpful AI assistant. When users ask
        general questions or have conversations that don't require specialized tools,
        you handle them directly.

        You're knowledgeable, conversational, and helpful. You provide clear, concise
        answers and engage naturally.

        However, you're also smart about delegation. When users ask about:
        - Remembering something → You suggest using the Memory Keeper
        - Tasks or reminders → You suggest the Task Coordinator
        - Calendar or scheduling → You suggest the Calendar Coordinator

        You have access to the user's memory context, so you can personalize responses
        based on what you know about them.""",
        tools=[
            MemorySearchTool(),
            MemoryContextTool(),
        ],
        llm=get_llm(),
        verbose=True,
        allow_delegation=True,  # Can delegate to other agents
    )


# ============================================
# Profile Agent - Manages User Preferences
# ============================================

def create_profile_agent() -> Agent:
    """
    Profile Agent manages user preferences and settings.

    Responsibilities:
    - Track dietary preferences
    - Store habits and routines
    - Manage user settings
    - Personalization preferences
    """
    return Agent(
        role="Profile Manager",
        goal="Manage user preferences, habits, and personalization settings",
        backstory="""You are Jenny's profile and preference manager. You help users set
        and update their preferences for personalized assistance.

        You handle:
        - Dietary preferences (vegetarian, allergies, favorite foods)
        - Daily routines and habits
        - Communication preferences
        - Timezone and location settings
        - Personal interests and hobbies

        You use Mem0 to persistently store this information, making Jenny more
        personalized and helpful over time.""",
        tools=[
            MemorySearchTool(),
            MemoryAddTool(),
            MemoryContextTool(),
        ],
        llm=get_llm(),
        verbose=True,
        allow_delegation=False,
    )


# ============================================
# Router Agent - Intelligent Query Router
# ============================================

def create_router_agent() -> Agent:
    """
    Router Agent analyzes queries and determines the best agent to handle them.

    This agent doesn't execute tasks - it only decides routing.
    """
    return Agent(
        role="Query Router",
        goal="Analyze user queries and route them to the most appropriate specialist agent",
        backstory="""You are Jenny's intelligent routing system. You analyze what users
        ask for and decide which specialist should handle it.

        You consider:
        - Is this about remembering/recalling? → Memory Keeper
        - Is this about tasks/reminders/todos? → Task Coordinator
        - Is this about calendar/scheduling/events? → Calendar Coordinator
        - Is this about user preferences/profile? → Profile Manager
        - Is this general conversation/questions? → General Assistant

        You make fast, accurate routing decisions to ensure users get the best help.""",
        tools=[],  # Router doesn't need tools
        llm=get_llm(),
        verbose=True,
        allow_delegation=True,
    )


# ============================================
# Factory function to get all agents
# ============================================

def get_all_agents() -> dict[str, Agent]:
    """Get all agents as a dictionary."""
    return {
        "memory": create_memory_agent(),
        "task": create_task_agent(),
        "calendar": create_calendar_agent(),
        "profile": create_profile_agent(),
        "general": create_general_agent(),
    }


__all__ = [
    "create_memory_agent",
    "create_task_agent",
    "create_calendar_agent",
    "create_profile_agent",
    "create_general_agent",
    "create_router_agent",
    "get_all_agents",
]
