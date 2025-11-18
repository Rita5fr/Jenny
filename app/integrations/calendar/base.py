"""
Base protocol for calendar providers.

This module defines the interface that all calendar providers must implement.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol


class CalendarEvent(Dict[str, Any]):
    """
    Dictionary representing a calendar event.

    Common fields:
        - id: Unique event identifier
        - title: Event title/summary
        - description: Event description
        - start: Start datetime
        - end: End datetime
        - location: Event location
        - attendees: List of attendee emails
        - organizer: Organizer email
        - all_day: Boolean indicating all-day event
        - recurrence: Recurrence rules (optional)
        - reminder_minutes: Minutes before event to remind (optional)
    """

    pass


class CalendarProvider(Protocol):
    """
    Protocol defining the interface for calendar providers.

    All calendar providers (Google, Outlook, Apple) must implement this interface.
    """

    async def list_events(
        self,
        start: datetime,
        end: datetime,
        max_results: int = 100,
    ) -> List[CalendarEvent]:
        """
        List calendar events within a time range.

        Args:
            start: Start datetime for event search
            end: End datetime for event search
            max_results: Maximum number of events to return

        Returns:
            List of calendar events
        """
        ...

    async def create_event(
        self,
        title: str,
        start: datetime,
        end: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        reminder_minutes: Optional[int] = None,
        all_day: bool = False,
    ) -> CalendarEvent:
        """
        Create a new calendar event.

        Args:
            title: Event title
            start: Start datetime
            end: End datetime
            description: Event description (optional)
            location: Event location (optional)
            attendees: List of attendee emails (optional)
            reminder_minutes: Minutes before event to send reminder (optional)
            all_day: Whether this is an all-day event

        Returns:
            Created calendar event
        """
        ...

    async def update_event(
        self,
        event_id: str,
        title: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
    ) -> CalendarEvent:
        """
        Update an existing calendar event.

        Args:
            event_id: ID of the event to update
            title: New title (optional)
            start: New start datetime (optional)
            end: New end datetime (optional)
            description: New description (optional)
            location: New location (optional)
            attendees: New attendee list (optional)

        Returns:
            Updated calendar event
        """
        ...

    async def delete_event(self, event_id: str) -> bool:
        """
        Delete a calendar event.

        Args:
            event_id: ID of the event to delete

        Returns:
            True if successful, False otherwise
        """
        ...

    async def get_event(self, event_id: str) -> Optional[CalendarEvent]:
        """
        Get a specific calendar event by ID.

        Args:
            event_id: ID of the event to retrieve

        Returns:
            Calendar event if found, None otherwise
        """
        ...

    async def search_events(
        self,
        query: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        max_results: int = 20,
    ) -> List[CalendarEvent]:
        """
        Search for events matching a query.

        Args:
            query: Search query string
            start: Optional start datetime for search range
            end: Optional end datetime for search range
            max_results: Maximum number of results

        Returns:
            List of matching calendar events
        """
        ...


__all__ = ["CalendarProvider", "CalendarEvent"]
