"""
Calendar agent for managing events across Google, Outlook, and Apple Calendar.

This agent handles:
- Listing upcoming events
- Creating new events from natural language
- Updating existing events
- Deleting events
- Searching for events
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from app.integrations.calendar import get_calendar_service

logger = logging.getLogger(__name__)


def parse_datetime_from_text(text: str) -> Optional[datetime]:
    """
    Parse datetime from natural language text.

    Examples:
        - "tomorrow at 3pm" -> tomorrow 15:00
        - "next monday at 10am" -> next monday 10:00
        - "in 2 hours" -> current time + 2 hours
    """
    text_lower = text.lower()
    now = datetime.now()

    # Tomorrow
    if "tomorrow" in text_lower:
        date = now + timedelta(days=1)

        # Extract time if present
        time_match = re.search(r"(\d{1,2})\s*(am|pm)", text_lower)
        if time_match:
            hour = int(time_match.group(1))
            meridiem = time_match.group(2)
            if meridiem == "pm" and hour != 12:
                hour += 12
            elif meridiem == "am" and hour == 12:
                hour = 0
            return date.replace(hour=hour, minute=0, second=0, microsecond=0)

        return date.replace(hour=9, minute=0, second=0, microsecond=0)

    # Today
    if "today" in text_lower:
        time_match = re.search(r"(\d{1,2})\s*(am|pm)", text_lower)
        if time_match:
            hour = int(time_match.group(1))
            meridiem = time_match.group(2)
            if meridiem == "pm" and hour != 12:
                hour += 12
            elif meridiem == "am" and hour == 12:
                hour = 0
            return now.replace(hour=hour, minute=0, second=0, microsecond=0)

    # In X hours/minutes
    if "in" in text_lower:
        hours_match = re.search(r"in\s+(\d+)\s+hour", text_lower)
        if hours_match:
            hours = int(hours_match.group(1))
            return now + timedelta(hours=hours)

        minutes_match = re.search(r"in\s+(\d+)\s+minute", text_lower)
        if minutes_match:
            minutes = int(minutes_match.group(1))
            return now + timedelta(minutes=minutes)

    # Default: 1 hour from now
    return now + timedelta(hours=1)


def extract_event_details(query: str) -> Dict[str, Any]:
    """
    Extract event details from natural language query.

    Returns:
        Dictionary with title, start, end, description, location
    """
    query_lower = query.lower()

    details: Dict[str, Any] = {}

    # Extract title (text before "at" or "on")
    title_match = re.search(r"(?:create|add|schedule)\s+(?:an?\s+)?(?:event\s+)?(?:for\s+)?(.+?)\s+(?:at|on|tomorrow|today)", query_lower, re.IGNORECASE)
    if title_match:
        details["title"] = title_match.group(1).strip()
    else:
        details["title"] = "New Event"

    # Extract start time
    details["start"] = parse_datetime_from_text(query)

    # Default duration: 1 hour
    if details["start"]:
        details["end"] = details["start"] + timedelta(hours=1)

    # Extract location
    location_match = re.search(r"(?:at|in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", query)
    if location_match:
        details["location"] = location_match.group(1)

    return details


async def calendar_agent(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle calendar-related queries.

    Args:
        query: User query (e.g., "What's on my calendar tomorrow?", "Schedule a meeting")
        context: Context dictionary with user_id, etc.

    Returns:
        Dictionary with agent response
    """
    user_id = context.get("user_id", "anonymous")
    query_lower = query.lower()

    try:
        calendar = get_calendar_service(user_id=user_id)

        # List events
        if any(word in query_lower for word in ["what's", "whats", "show", "list", "upcoming", "schedule"]):
            # Determine time range
            if "tomorrow" in query_lower:
                start = datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1)
                end = start + timedelta(days=1)
                time_desc = "tomorrow"
            elif "today" in query_lower:
                start = datetime.now().replace(hour=0, minute=0, second=0)
                end = start + timedelta(days=1)
                time_desc = "today"
            elif "week" in query_lower or "this week" in query_lower:
                start = datetime.now()
                end = start + timedelta(days=7)
                time_desc = "this week"
            else:
                start = datetime.now()
                end = start + timedelta(days=1)
                time_desc = "today"

            events = await calendar.list_events(start=start, end=end, max_results=10)

            if not events:
                return {"reply": f"You have no events scheduled for {time_desc}."}

            # Format events
            event_list = []
            for event in events:
                title = event.get("title", "Untitled")
                start_time = event.get("start", "")
                provider = event.get("provider", "unknown")

                # Simple time formatting
                try:
                    start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    time_str = start_dt.strftime("%I:%M %p")
                except:
                    time_str = start_time

                event_list.append(f"- {title} at {time_str} ({provider})")

            events_text = "\n".join(event_list)
            return {"reply": f"Your events for {time_desc}:\n{events_text}"}

        # Create event
        elif any(word in query_lower for word in ["create", "add", "schedule", "book", "set up"]):
            event_details = extract_event_details(query)

            event = await calendar.create_event(
                title=event_details.get("title", "New Event"),
                start=event_details["start"],
                end=event_details["end"],
                description=f"Created by Jenny from: {query}",
                location=event_details.get("location"),
            )

            if event:
                start_time = event_details["start"].strftime("%I:%M %p on %B %d")
                return {
                    "reply": f"I've created an event '{event_details['title']}' for {start_time}."
                }
            else:
                return {
                    "reply": "I couldn't create the event. Please make sure your calendar is connected."
                }

        # Search events
        elif any(word in query_lower for word in ["find", "search"]):
            # Extract search query
            search_match = re.search(r"(?:find|search)\s+(?:for\s+)?(.+)", query_lower)
            if search_match:
                search_query = search_match.group(1).strip()
                events = await calendar.search_events(search_query, max_results=5)

                if not events:
                    return {"reply": f"I couldn't find any events matching '{search_query}'."}

                event_list = []
                for event in events:
                    title = event.get("title", "Untitled")
                    start_time = event.get("start", "")
                    event_list.append(f"- {title} at {start_time}")

                events_text = "\n".join(event_list)
                return {"reply": f"Found these events:\n{events_text}"}

        # Sync calendars
        elif "sync" in query_lower:
            sync_status = await calendar.sync_all_calendars()

            connected = [name for name, status in sync_status.items() if status.get("connected")]
            if connected:
                return {
                    "reply": f"Calendars synced! Connected: {', '.join(connected)}"
                }
            else:
                return {
                    "reply": "No calendars are currently connected. Please connect your calendars first."
                }

        # Default response
        else:
            return {
                "reply": "I can help you with your calendar. Try asking:\n"
                "- 'What's on my calendar today?'\n"
                "- 'Schedule a meeting tomorrow at 2pm'\n"
                "- 'Find events about project'"
            }

    except Exception as exc:
        logger.exception(f"Calendar agent error: {exc}")
        return {
            "reply": "I had trouble accessing your calendar. Please make sure it's connected.",
            "error": str(exc),
        }


__all__ = ["calendar_agent"]
