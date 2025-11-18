"""
Apple Calendar (iCloud) integration via CalDAV.

This module provides integration with Apple Calendar using the CalDAV protocol.

Setup:
    1. Generate an app-specific password for iCloud
    2. Store credentials securely

Usage:
    from app.integrations.calendar.apple_calendar import AppleCalendarProvider

    calendar = AppleCalendarProvider(
        user_id="user_123",
        apple_id="user@icloud.com",
        app_password="xxxx-xxxx-xxxx-xxxx"
    )
    await calendar.connect()
    events = await calendar.list_events(start=datetime.now(), end=datetime.now() + timedelta(days=7))
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.integrations.calendar.base import CalendarEvent

logger = logging.getLogger(__name__)

# Flag for CalDAV availability
CALDAV_AVAILABLE = False

try:
    import caldav
    from caldav.elements import dav, cdav

    CALDAV_AVAILABLE = True
    logger.info("CalDAV library loaded successfully")
except ImportError:
    logger.warning("CalDAV not available. Install with: pip install caldav")


class AppleCalendarProvider:
    """Apple Calendar (iCloud) provider using CalDAV."""

    # iCloud CalDAV server
    CALDAV_URL = "https://caldav.icloud.com"

    def __init__(self, user_id: str, apple_id: Optional[str] = None, app_password: Optional[str] = None):
        """
        Initialize Apple Calendar provider.

        Args:
            user_id: User identifier
            apple_id: Apple ID email (e.g., user@icloud.com)
            app_password: App-specific password from iCloud settings
        """
        self.user_id = user_id
        self.apple_id = apple_id
        self.app_password = app_password
        self.client = None
        self.principal = None
        self.calendar = None

    async def connect(self) -> bool:
        """
        Connect to Apple Calendar via CalDAV.

        Returns:
            True if connection successful
        """
        if not CALDAV_AVAILABLE:
            logger.error("CalDAV library not available")
            return False

        if not self.apple_id or not self.app_password:
            logger.error("Apple ID and app password required")
            return False

        try:
            # Create CalDAV client
            self.client = caldav.DAVClient(
                url=self.CALDAV_URL,
                username=self.apple_id,
                password=self.app_password,
            )

            # Get principal
            self.principal = self.client.principal()

            # Get default calendar
            calendars = self.principal.calendars()
            if calendars:
                self.calendar = calendars[0]  # Use first calendar
                logger.info(f"Connected to Apple Calendar for user {self.user_id}")
                return True
            else:
                logger.error("No calendars found")
                return False

        except Exception as exc:
            logger.exception(f"Failed to connect to Apple Calendar: {exc}")
            return False

    async def list_events(
        self,
        start: datetime,
        end: datetime,
        max_results: int = 100,
    ) -> List[CalendarEvent]:
        """List events from Apple Calendar."""
        if not self.calendar:
            logger.error("Not connected to calendar")
            return []

        try:
            events = self.calendar.date_search(
                start=start,
                end=end,
                expand=True,
            )

            result = []
            for event in events[:max_results]:
                try:
                    ical = event.icalendar_component
                    result.append(self._convert_to_calendar_event(ical, event.id))
                except Exception as exc:
                    logger.warning(f"Failed to parse event: {exc}")
                    continue

            return result

        except Exception as exc:
            logger.exception(f"Failed to list Apple Calendar events: {exc}")
            return []

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
    ) -> Optional[CalendarEvent]:
        """Create a new event in Apple Calendar."""
        if not self.calendar:
            logger.error("Not connected to calendar")
            return None

        try:
            from icalendar import Calendar, Event as ICalEvent, Alarm

            # Create iCalendar event
            cal = Calendar()
            event = ICalEvent()

            event.add("summary", title)
            event.add("dtstart", start)
            event.add("dtend", end)

            if description:
                event.add("description", description)

            if location:
                event.add("location", location)

            if attendees:
                for attendee_email in attendees:
                    event.add("attendee", f"mailto:{attendee_email}")

            if reminder_minutes is not None:
                alarm = Alarm()
                alarm.add("action", "DISPLAY")
                alarm.add("trigger", timedelta(minutes=-reminder_minutes))
                event.add_component(alarm)

            cal.add_component(event)

            # Save to CalDAV server
            created_event = self.calendar.save_event(cal.to_ical())

            logger.info(f"Created Apple Calendar event: {created_event.id}")

            # Return the created event
            ical = created_event.icalendar_component
            return self._convert_to_calendar_event(ical, created_event.id)

        except Exception as exc:
            logger.exception(f"Failed to create Apple Calendar event: {exc}")
            return None

    async def update_event(
        self,
        event_id: str,
        title: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
    ) -> Optional[CalendarEvent]:
        """Update an existing Apple Calendar event."""
        if not self.calendar:
            logger.error("Not connected to calendar")
            return None

        try:
            # Get the event
            event = self.calendar.event_by_uid(event_id)
            ical = event.icalendar_component

            # Update fields
            if title:
                ical["SUMMARY"] = title
            if start:
                ical["DTSTART"].dt = start
            if end:
                ical["DTEND"].dt = end
            if description:
                ical["DESCRIPTION"] = description
            if location:
                ical["LOCATION"] = location

            # Save updated event
            event.save()

            logger.info(f"Updated Apple Calendar event: {event_id}")
            return self._convert_to_calendar_event(ical, event_id)

        except Exception as exc:
            logger.exception(f"Failed to update Apple Calendar event: {exc}")
            return None

    async def delete_event(self, event_id: str) -> bool:
        """Delete an Apple Calendar event."""
        if not self.calendar:
            logger.error("Not connected to calendar")
            return False

        try:
            event = self.calendar.event_by_uid(event_id)
            event.delete()

            logger.info(f"Deleted Apple Calendar event: {event_id}")
            return True

        except Exception as exc:
            logger.exception(f"Failed to delete Apple Calendar event: {exc}")
            return False

    async def get_event(self, event_id: str) -> Optional[CalendarEvent]:
        """Get a specific Apple Calendar event."""
        if not self.calendar:
            logger.error("Not connected to calendar")
            return None

        try:
            event = self.calendar.event_by_uid(event_id)
            ical = event.icalendar_component
            return self._convert_to_calendar_event(ical, event_id)

        except Exception as exc:
            logger.exception(f"Failed to get Apple Calendar event: {exc}")
            return None

    async def search_events(
        self,
        query: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        max_results: int = 20,
    ) -> List[CalendarEvent]:
        """
        Search Apple Calendar events.

        Note: CalDAV doesn't support text search natively,
        so we fetch events in the time range and filter by query.
        """
        if not start:
            start = datetime.now()
        if not end:
            end = start + timedelta(days=365)  # Search 1 year ahead

        all_events = await self.list_events(start, end, max_results=max_results * 2)

        # Filter by query (simple text matching)
        query_lower = query.lower()
        filtered = []

        for event in all_events:
            title = event.get("title", "").lower()
            description = event.get("description", "").lower()

            if query_lower in title or query_lower in description:
                filtered.append(event)

            if len(filtered) >= max_results:
                break

        return filtered

    def _convert_to_calendar_event(self, ical_event: Any, event_id: str) -> CalendarEvent:
        """Convert iCalendar event to standard CalendarEvent format."""
        try:
            start = ical_event.get("DTSTART").dt if ical_event.get("DTSTART") else None
            end = ical_event.get("DTEND").dt if ical_event.get("DTEND") else None

            # Parse attendees
            attendees = []
            if "ATTENDEE" in ical_event:
                attendee_data = ical_event.get("ATTENDEE")
                if isinstance(attendee_data, list):
                    for att in attendee_data:
                        email = str(att).replace("mailto:", "")
                        attendees.append(email)
                else:
                    email = str(attendee_data).replace("mailto:", "")
                    attendees.append(email)

            return CalendarEvent(
                {
                    "id": event_id,
                    "title": str(ical_event.get("SUMMARY", "")),
                    "description": str(ical_event.get("DESCRIPTION", "")),
                    "start": start.isoformat() if start else None,
                    "end": end.isoformat() if end else None,
                    "location": str(ical_event.get("LOCATION", "")),
                    "attendees": attendees,
                    "organizer": str(ical_event.get("ORGANIZER", "")).replace("mailto:", ""),
                    "all_day": not hasattr(start, "hour") if start else False,
                    "provider": "apple",
                    "raw": ical_event,
                }
            )

        except Exception as exc:
            logger.exception(f"Failed to convert iCalendar event: {exc}")
            return CalendarEvent({"id": event_id, "title": "Unknown", "provider": "apple"})


__all__ = ["AppleCalendarProvider"]
