"""CrewAI Tools for Jenny - Wraps existing functionality for CrewAI agents."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from crewai_tools import BaseTool
from pydantic import BaseModel, Field

# Import utility functions
from app.services.memory_utils import add_memory, search_memory, get_user_context
from app.services.tasks import create_task, list_tasks, complete_task, delete_task
from app.integrations.calendar import get_calendar_service
from app.services.calendar_auth import is_calendar_connected
from app.integrations.calendar.google_calendar import GoogleCalendarProvider


# ============================================
# Memory Tools (Mem0 Integration)
# ============================================

class MemorySearchInput(BaseModel):
    """Input schema for memory search."""
    query: str = Field(..., description="Search query for memories")
    user_id: str = Field(..., description="User ID to search memories for")
    limit: int = Field(5, description="Maximum number of results")


class MemoryAddInput(BaseModel):
    """Input schema for adding memory."""
    text: str = Field(..., description="Text to remember")
    user_id: str = Field(..., description="User ID to add memory for")


class MemorySearchTool(BaseTool):
    name: str = "search_user_memory"
    description: str = """Search through user's long-term memory stored in Mem0.
    Use this to find what the user told you before, their preferences, habits, or any past conversations.
    Examples: 'What does the user like?', 'What are user's dietary preferences?'"""
    args_schema: type[BaseModel] = MemorySearchInput

    def _run(self, query: str, user_id: str, limit: int = 5) -> str:
        """Search user memory synchronously."""
        try:
            result = asyncio.run(search_memory(query, user_id, k=limit))

            if result.get("results"):
                memories = result["results"]
                formatted = "\n".join([f"- {mem.get('memory', mem)}" for mem in memories[:limit]])
                return f"Found {len(memories)} relevant memories:\n{formatted}"
            return "No relevant memories found."
        except Exception as exc:
            return f"Error searching memory: {exc}"


class MemoryAddTool(BaseTool):
    name: str = "add_to_user_memory"
    description: str = """Add important information to user's long-term memory in Mem0.
    Use this to remember user preferences, important facts, or things they want you to remember.
    Examples: 'User loves Italian food', 'User prefers morning meetings', 'User's birthday is March 15'"""
    args_schema: type[BaseModel] = MemoryAddInput

    def _run(self, text: str, user_id: str) -> str:
        """Add to user memory synchronously."""
        try:
            result = asyncio.run(add_memory(text, user_id))
            return f"✓ Remembered: {text}"
        except Exception as exc:
            return f"Error saving memory: {exc}"


class MemoryContextTool(BaseTool):
    name: str = "get_user_context"
    description: str = """Get all stored context and memories for a user from Mem0.
    Use this to get a comprehensive view of what you know about the user."""

    class ContextInput(BaseModel):
        user_id: str = Field(..., description="User ID to get context for")

    args_schema: type[BaseModel] = ContextInput

    def _run(self, user_id: str) -> str:
        """Get user context synchronously."""
        try:
            result = asyncio.run(get_user_context(user_id))

            if result.get("results"):
                memories = result["results"]
                formatted = "\n".join([f"- {mem.get('memory', mem)}" for mem in memories])
                return f"User context ({len(memories)} items):\n{formatted}"
            return "No stored context found for this user."
        except Exception as exc:
            return f"Error getting context: {exc}"


# ============================================
# Task Tools (Reminders, TODOs)
# ============================================

class TaskCreateInput(BaseModel):
    """Input schema for creating a task."""
    user_id: str = Field(..., description="User ID")
    title: str = Field(..., description="Task title")
    details: Optional[str] = Field(None, description="Task details/description")
    due_at: Optional[str] = Field(None, description="Due date/time in ISO format (YYYY-MM-DD HH:MM:SS)")
    recurrence: Optional[str] = Field(None, description="Recurrence pattern: daily, weekly, monthly")


class TaskListInput(BaseModel):
    """Input schema for listing tasks."""
    user_id: str = Field(..., description="User ID")
    limit: int = Field(10, description="Maximum number of tasks to return")


class TaskCompleteInput(BaseModel):
    """Input schema for completing a task."""
    task_id: str = Field(..., description="Task ID (UUID)")
    user_id: str = Field(..., description="User ID")


class TaskDeleteInput(BaseModel):
    """Input schema for deleting a task."""
    task_id: str = Field(..., description="Task ID (UUID)")
    user_id: str = Field(..., description="User ID")


class TaskCreateTool(BaseTool):
    name: str = "create_task"
    description: str = """Create a new task or reminder for the user.
    Use this for reminders, todos, or any scheduled tasks.
    Examples: 'Remind me to call mom tomorrow', 'Add task to review report by Friday'"""
    args_schema: type[BaseModel] = TaskCreateInput

    def _run(self, user_id: str, title: str, details: Optional[str] = None,
             due_at: Optional[str] = None, recurrence: Optional[str] = None) -> str:
        """Create task synchronously."""
        try:
            # Parse due_at if provided
            due_datetime = None
            if due_at:
                try:
                    due_datetime = datetime.fromisoformat(due_at)
                except:
                    # Try parsing natural language dates
                    if "tomorrow" in due_at.lower():
                        due_datetime = datetime.now() + timedelta(days=1)
                    elif "today" in due_at.lower():
                        due_datetime = datetime.now()
                    elif "next week" in due_at.lower():
                        due_datetime = datetime.now() + timedelta(days=7)

            result = asyncio.run(create_task(user_id, title, details, due_datetime, recurrence))

            response = f"✓ Task created: {result['title']}"
            if result.get('due_at'):
                response += f" (due: {result['due_at']})"
            if result.get('recurrence'):
                response += f" [Recurs: {result['recurrence']}]"

            return response
        except Exception as exc:
            return f"Error creating task: {exc}"


class TaskListTool(BaseTool):
    name: str = "list_tasks"
    description: str = """List all pending tasks and reminders for the user.
    Use this to show what tasks the user has, or to check their todo list."""
    args_schema: type[BaseModel] = TaskListInput

    def _run(self, user_id: str, limit: int = 10) -> str:
        """List tasks synchronously."""
        try:
            tasks = asyncio.run(list_tasks(user_id, limit))

            if not tasks:
                return "You have no pending tasks."

            formatted = []
            for task in tasks:
                line = f"• {task['title']}"
                if task.get('due_at'):
                    line += f" (due: {task['due_at']})"
                line += f" [ID: {task['id'][:8]}...]"
                formatted.append(line)

            return f"Your tasks ({len(tasks)}):\n" + "\n".join(formatted)
        except Exception as exc:
            return f"Error listing tasks: {exc}"


class TaskCompleteTool(BaseTool):
    name: str = "complete_task"
    description: str = """Mark a task as completed.
    Use this when user says they finished a task or want to mark it done."""
    args_schema: type[BaseModel] = TaskCompleteInput

    def _run(self, task_id: str, user_id: str) -> str:
        """Complete task synchronously."""
        try:
            result = asyncio.run(complete_task(task_id, user_id))
            if result:
                return f"✓ Completed task: {result['title']}"
            return "Task not found."
        except Exception as exc:
            return f"Error completing task: {exc}"


class TaskDeleteTool(BaseTool):
    name: str = "delete_task"
    description: str = """Delete a task permanently.
    Use this when user wants to remove a task completely."""
    args_schema: type[BaseModel] = TaskDeleteInput

    def _run(self, task_id: str, user_id: str) -> str:
        """Delete task synchronously."""
        try:
            deleted = asyncio.run(delete_task(task_id, user_id))
            if deleted:
                return "✓ Task deleted"
            return "Task not found."
        except Exception as exc:
            return f"Error deleting task: {exc}"


# ============================================
# Calendar Tools
# ============================================

class CalendarListEventsInput(BaseModel):
    """Input schema for listing calendar events."""
    user_id: str = Field(..., description="User ID")
    days_ahead: int = Field(1, description="Number of days to look ahead (1 = today, 7 = this week)")


class CalendarCreateEventInput(BaseModel):
    """Input schema for creating calendar event."""
    user_id: str = Field(..., description="User ID")
    title: str = Field(..., description="Event title")
    start_time: str = Field(..., description="Start time in ISO format or natural language (e.g., 'tomorrow at 2pm')")
    duration_hours: int = Field(1, description="Event duration in hours")
    description: Optional[str] = Field(None, description="Event description")
    location: Optional[str] = Field(None, description="Event location")


class CalendarSearchEventsInput(BaseModel):
    """Input schema for searching calendar events."""
    user_id: str = Field(..., description="User ID")
    query: str = Field(..., description="Search query")


class CalendarListEventsTool(BaseTool):
    name: str = "list_calendar_events"
    description: str = """List upcoming calendar events for the user.
    Use this to show what's on user's calendar today, tomorrow, or this week.
    Searches across Google Calendar, Outlook, and Apple Calendar."""
    args_schema: type[BaseModel] = CalendarListEventsInput

    def _run(self, user_id: str, days_ahead: int = 1) -> str:
        """List calendar events synchronously."""
        try:
            calendar = get_calendar_service(user_id=user_id)

            start = datetime.now()
            end = start + timedelta(days=days_ahead)

            events = asyncio.run(calendar.list_events(start=start, end=end, max_results=10))

            if not events:
                period = "today" if days_ahead == 1 else f"the next {days_ahead} days"
                return f"No events scheduled for {period}."

            formatted = []
            for event in events:
                title = event.get("title", "Untitled")
                start_time = event.get("start", "")
                provider = event.get("provider", "")

                try:
                    start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    time_str = start_dt.strftime("%b %d at %I:%M %p")
                except:
                    time_str = start_time

                formatted.append(f"• {title} - {time_str} ({provider})")

            return f"Upcoming events ({len(events)}):\n" + "\n".join(formatted)
        except Exception as exc:
            return f"Error listing calendar events: {exc}"


class CalendarCreateEventTool(BaseTool):
    name: str = "create_calendar_event"
    description: str = """Create a new calendar event.
    Use this to schedule meetings, appointments, or any calendar events.
    Works with Google Calendar, Outlook, and Apple Calendar."""
    args_schema: type[BaseModel] = CalendarCreateEventInput

    def _run(self, user_id: str, title: str, start_time: str,
             duration_hours: int = 1, description: Optional[str] = None,
             location: Optional[str] = None) -> str:
        """Create calendar event synchronously."""
        try:
            # Check if Google Calendar is connected
            is_connected = asyncio.run(is_calendar_connected(user_id, "google"))

            if not is_connected:
                # Generate OAuth URL for the user to connect
                try:
                    google_calendar = GoogleCalendarProvider(user_id=user_id)
                    auth_url = google_calendar.get_authorization_url()

                    return (
                        f"📅 To create calendar events, please connect your Google Calendar first!\n\n"
                        f"Click this link to connect:\n{auth_url}\n\n"
                        f"After connecting, I'll be able to create '{title}' and other events for you."
                    )
                except Exception as e:
                    return (
                        f"📅 Google Calendar is not connected. "
                        f"Please ask the user to connect their calendar at /calendar/connect/google?user_id={user_id}"
                    )

            # Calendar is connected, proceed with creating event
            calendar = get_calendar_service(user_id=user_id)

            # Parse start time
            start_dt = None
            try:
                start_dt = datetime.fromisoformat(start_time)
            except:
                # Natural language parsing
                start_time_lower = start_time.lower()
                now = datetime.now()

                if "tomorrow" in start_time_lower:
                    start_dt = now + timedelta(days=1)
                    start_dt = start_dt.replace(hour=9, minute=0, second=0, microsecond=0)
                elif "today" in start_time_lower:
                    start_dt = now.replace(hour=9, minute=0, second=0, microsecond=0)
                elif "next week" in start_time_lower:
                    start_dt = now + timedelta(days=7)
                    start_dt = start_dt.replace(hour=9, minute=0, second=0, microsecond=0)
                else:
                    start_dt = now + timedelta(hours=1)

            end_dt = start_dt + timedelta(hours=duration_hours)

            event = asyncio.run(calendar.create_event(
                title=title,
                start=start_dt,
                end=end_dt,
                description=description,
                location=location
            ))

            if event:
                time_str = start_dt.strftime("%b %d at %I:%M %p")
                return f"✓ Created event: {title} on {time_str}"

            return "Failed to create event. Please try again."
        except Exception as exc:
            return f"Error creating calendar event: {exc}"


class CalendarSearchEventsTool(BaseTool):
    name: str = "search_calendar_events"
    description: str = """Search for specific events in user's calendar.
    Use this to find events by name, description, or other criteria."""
    args_schema: type[BaseModel] = CalendarSearchEventsInput

    def _run(self, user_id: str, query: str) -> str:
        """Search calendar events synchronously."""
        try:
            calendar = get_calendar_service(user_id=user_id)
            events = asyncio.run(calendar.search_events(query, max_results=5))

            if not events:
                return f"No events found matching '{query}'."

            formatted = []
            for event in events:
                title = event.get("title", "Untitled")
                start_time = event.get("start", "")
                formatted.append(f"• {title} - {start_time}")

            return f"Found {len(events)} event(s):\n" + "\n".join(formatted)
        except Exception as exc:
            return f"Error searching calendar: {exc}"


# ============================================
# Export all tools
# ============================================

def get_all_tools() -> List[BaseTool]:
    """Get all CrewAI tools for Jenny."""
    return [
        # Memory tools
        MemorySearchTool(),
        MemoryAddTool(),
        MemoryContextTool(),

        # Task tools
        TaskCreateTool(),
        TaskListTool(),
        TaskCompleteTool(),
        TaskDeleteTool(),

        # Calendar tools
        CalendarListEventsTool(),
        CalendarCreateEventTool(),
        CalendarSearchEventsTool(),
    ]


__all__ = [
    "get_all_tools",
    "MemorySearchTool",
    "MemoryAddTool",
    "MemoryContextTool",
    "TaskCreateTool",
    "TaskListTool",
    "TaskCompleteTool",
    "TaskDeleteTool",
    "CalendarListEventsTool",
    "CalendarCreateEventTool",
    "CalendarSearchEventsTool",
]
