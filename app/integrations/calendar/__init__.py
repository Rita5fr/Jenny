"""
Calendar integrations package.

Provides unified interface for:
- Google Calendar
- Microsoft Outlook/Office 365
- Apple Calendar (CalDAV)
"""

from app.integrations.calendar.unified import UnifiedCalendar, get_calendar_service

__all__ = ["UnifiedCalendar", "get_calendar_service"]
