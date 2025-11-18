"""
Unified Calendar Service.

This module provides a unified interface for all calendar providers,
allowing Jenny to work with Google Calendar, Microsoft Outlook, and Apple Calendar
through a single consistent API.

Usage:
    from app.integrations.calendar import get_calendar_service

    calendar = get_calendar_service(user_id="user_123")

    # List events from all connected calendars
    events = await calendar.list_all_events(start=datetime.now(), end=datetime.now() + timedelta(days=7))

    # Create event (uses primary calendar)
    event = await calendar.create_event(
        title="Team Meeting",
        start=datetime.now() + timedelta(hours=1),
        end=datetime.now() + timedelta(hours=2),
        description="Discuss Q1 goals"
    )
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.integrations.calendar.apple_calendar import AppleCalendarProvider
from app.integrations.calendar.base import CalendarEvent
from app.integrations.calendar.google_calendar import GoogleCalendarProvider
from app.integrations.calendar.microsoft_calendar import MicrosoftCalendarProvider

logger = logging.getLogger(__name__)


class UnifiedCalendar:
    """
    Unified calendar interface for all providers.

    This class manages multiple calendar providers and provides
    a unified interface to work with all of them.
    """

    def __init__(self, user_id: str):
        """
        Initialize unified calendar service.

        Args:
            user_id: User identifier
        """
        self.user_id = user_id
        self.providers: Dict[str, Any] = {}
        self.primary_provider: Optional[str] = None

        # Initialize providers (will be connected when credentials are available)
        self.providers["google"] = GoogleCalendarProvider(user_id=user_id)
        self.providers["microsoft"] = MicrosoftCalendarProvider(user_id=user_id)
        self.providers["apple"] = AppleCalendarProvider(user_id=user_id)

    def set_primary_provider(self, provider_name: str) -> None:
        """
        Set the primary calendar provider for creating events.

        Args:
            provider_name: Name of provider (google, microsoft, apple)
        """
        if provider_name in self.providers:
            self.primary_provider = provider_name
            logger.info(f"Primary calendar provider set to: {provider_name}")
        else:
            logger.error(f"Invalid provider name: {provider_name}")

    def get_provider(self, provider_name: str) -> Optional[Any]:
        """
        Get a specific calendar provider.

        Args:
            provider_name: Name of provider (google, microsoft, apple)

        Returns:
            Calendar provider instance or None
        """
        return self.providers.get(provider_name)

    async def list_all_events(
        self,
        start: datetime,
        end: datetime,
        max_results_per_provider: int = 50,
    ) -> Dict[str, List[CalendarEvent]]:
        """
        List events from all connected calendar providers.

        Args:
            start: Start datetime for event search
            end: End datetime for event search
            max_results_per_provider: Max results per provider

        Returns:
            Dictionary mapping provider names to event lists
        """
        all_events: Dict[str, List[CalendarEvent]] = {}

        for provider_name, provider in self.providers.items():
            try:
                events = await provider.list_events(
                    start=start,
                    end=end,
                    max_results=max_results_per_provider,
                )
                all_events[provider_name] = events
                logger.debug(f"Retrieved {len(events)} events from {provider_name}")
            except Exception as exc:
                logger.warning(f"Failed to list events from {provider_name}: {exc}")
                all_events[provider_name] = []

        return all_events

    async def list_events(
        self,
        start: datetime,
        end: datetime,
        provider_name: Optional[str] = None,
        max_results: int = 100,
    ) -> List[CalendarEvent]:
        """
        List events from a specific provider or all providers (merged).

        Args:
            start: Start datetime
            end: End datetime
            provider_name: Specific provider name (None for all)
            max_results: Maximum results

        Returns:
            List of calendar events
        """
        if provider_name:
            provider = self.get_provider(provider_name)
            if provider:
                return await provider.list_events(start, end, max_results)
            return []

        # Merge events from all providers
        all_events_dict = await self.list_all_events(start, end, max_results)
        merged_events = []

        for events in all_events_dict.values():
            merged_events.extend(events)

        # Sort by start time
        merged_events.sort(key=lambda e: e.get("start", ""))

        return merged_events[:max_results]

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
        provider_name: Optional[str] = None,
    ) -> Optional[CalendarEvent]:
        """
        Create an event in a calendar provider.

        Args:
            title: Event title
            start: Start datetime
            end: End datetime
            description: Event description
            location: Event location
            attendees: List of attendee emails
            reminder_minutes: Minutes before event to remind
            all_day: Whether this is an all-day event
            provider_name: Provider to use (None for primary)

        Returns:
            Created calendar event or None
        """
        provider_to_use = provider_name or self.primary_provider or "google"
        provider = self.get_provider(provider_to_use)

        if not provider:
            logger.error(f"Provider {provider_to_use} not available")
            return None

        try:
            event = await provider.create_event(
                title=title,
                start=start,
                end=end,
                description=description,
                location=location,
                attendees=attendees,
                reminder_minutes=reminder_minutes,
                all_day=all_day,
            )
            logger.info(f"Created event '{title}' using {provider_to_use}")
            return event

        except Exception as exc:
            logger.exception(f"Failed to create event: {exc}")
            return None

    async def update_event(
        self,
        event_id: str,
        provider_name: str,
        title: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
    ) -> Optional[CalendarEvent]:
        """
        Update an existing calendar event.

        Args:
            event_id: Event ID
            provider_name: Provider where the event exists
            title: New title
            start: New start datetime
            end: New end datetime
            description: New description
            location: New location
            attendees: New attendee list

        Returns:
            Updated event or None
        """
        provider = self.get_provider(provider_name)
        if not provider:
            logger.error(f"Provider {provider_name} not available")
            return None

        try:
            event = await provider.update_event(
                event_id=event_id,
                title=title,
                start=start,
                end=end,
                description=description,
                location=location,
                attendees=attendees,
            )
            logger.info(f"Updated event {event_id} in {provider_name}")
            return event

        except Exception as exc:
            logger.exception(f"Failed to update event: {exc}")
            return None

    async def delete_event(self, event_id: str, provider_name: str) -> bool:
        """
        Delete a calendar event.

        Args:
            event_id: Event ID
            provider_name: Provider where the event exists

        Returns:
            True if successful
        """
        provider = self.get_provider(provider_name)
        if not provider:
            logger.error(f"Provider {provider_name} not available")
            return False

        try:
            success = await provider.delete_event(event_id)
            if success:
                logger.info(f"Deleted event {event_id} from {provider_name}")
            return success

        except Exception as exc:
            logger.exception(f"Failed to delete event: {exc}")
            return False

    async def search_events(
        self,
        query: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        max_results: int = 20,
        provider_name: Optional[str] = None,
    ) -> List[CalendarEvent]:
        """
        Search for events matching a query.

        Args:
            query: Search query
            start: Optional start datetime
            end: Optional end datetime
            max_results: Maximum results
            provider_name: Specific provider (None for all)

        Returns:
            List of matching events
        """
        if provider_name:
            provider = self.get_provider(provider_name)
            if provider:
                return await provider.search_events(query, start, end, max_results)
            return []

        # Search across all providers
        all_results = []

        for name, provider in self.providers.items():
            try:
                results = await provider.search_events(query, start, end, max_results)
                all_results.extend(results)
                logger.debug(f"Found {len(results)} events in {name}")
            except Exception as exc:
                logger.warning(f"Search failed in {name}: {exc}")
                continue

        # Sort by relevance/start time
        all_results.sort(key=lambda e: e.get("start", ""))

        return all_results[:max_results]

    async def sync_all_calendars(self) -> Dict[str, Any]:
        """
        Sync all connected calendars and return summary.

        Returns:
            Dictionary with sync status for each provider
        """
        sync_status = {}

        for name, provider in self.providers.items():
            try:
                # Check if provider is connected by trying to list events
                from datetime import timedelta

                start = datetime.now()
                end = start + timedelta(days=1)

                events = await provider.list_events(start, end, max_results=1)

                sync_status[name] = {
                    "connected": True,
                    "last_sync": datetime.now().isoformat(),
                    "status": "ok",
                }

            except Exception as exc:
                sync_status[name] = {
                    "connected": False,
                    "error": str(exc),
                    "status": "error",
                }

        return sync_status


# Singleton instance per user
_calendar_instances: Dict[str, UnifiedCalendar] = {}


def get_calendar_service(user_id: str) -> UnifiedCalendar:
    """
    Get or create a unified calendar service for a user.

    Args:
        user_id: User identifier

    Returns:
        UnifiedCalendar instance
    """
    if user_id not in _calendar_instances:
        _calendar_instances[user_id] = UnifiedCalendar(user_id=user_id)

    return _calendar_instances[user_id]


__all__ = ["UnifiedCalendar", "get_calendar_service"]
