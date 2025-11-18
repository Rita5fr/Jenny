"""
Google Calendar integration.

This module provides integration with Google Calendar API.

Setup:
    1. Create a project in Google Cloud Console
    2. Enable Google Calendar API
    3. Create OAuth 2.0 credentials
    4. Set environment variables:
        - GOOGLE_CALENDAR_CLIENT_ID
        - GOOGLE_CALENDAR_CLIENT_SECRET
        - GOOGLE_CALENDAR_REDIRECT_URI

Usage:
    from app.integrations.calendar.google_calendar import GoogleCalendarProvider

    calendar = GoogleCalendarProvider(user_id="user_123")
    await calendar.authenticate(auth_code="...")
    events = await calendar.list_events(start=datetime.now(), end=datetime.now() + timedelta(days=7))
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from app.integrations.calendar.base import CalendarEvent

logger = logging.getLogger(__name__)

load_dotenv()

# Google Calendar API configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CALENDAR_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_CALENDAR_REDIRECT_URI", "http://localhost:8044/auth/google/callback")

SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Flag for Google API availability
GOOGLE_CALENDAR_AVAILABLE = False

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build

    GOOGLE_CALENDAR_AVAILABLE = True
    logger.info("Google Calendar API library loaded successfully")
except ImportError:
    logger.warning(
        "Google Calendar API not available. Install with: "
        "pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
    )


class GoogleCalendarProvider:
    """Google Calendar provider implementation."""

    def __init__(self, user_id: str):
        """
        Initialize Google Calendar provider.

        Args:
            user_id: User identifier (used to store/retrieve credentials)
        """
        self.user_id = user_id
        self.service = None
        self.credentials = None

    def get_authorization_url(self) -> str:
        """
        Get the authorization URL for OAuth 2.0 flow.

        Returns:
            Authorization URL for user to visit
        """
        if not GOOGLE_CALENDAR_AVAILABLE:
            raise RuntimeError("Google Calendar API not available")

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI,
        )

        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
        )

        return authorization_url

    async def authenticate(self, auth_code: str) -> bool:
        """
        Authenticate using authorization code from OAuth flow.

        Args:
            auth_code: Authorization code from OAuth callback

        Returns:
            True if authentication successful
        """
        if not GOOGLE_CALENDAR_AVAILABLE:
            raise RuntimeError("Google Calendar API not available")

        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": GOOGLE_CLIENT_ID,
                        "client_secret": GOOGLE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                },
                scopes=SCOPES,
                redirect_uri=GOOGLE_REDIRECT_URI,
            )

            flow.fetch_token(code=auth_code)
            self.credentials = flow.credentials

            # Build the service
            self.service = build("calendar", "v3", credentials=self.credentials)

            # TODO: Store credentials securely for this user
            # For now, credentials are only in memory

            logger.info(f"Google Calendar authenticated for user {self.user_id}")
            return True

        except Exception as exc:
            logger.exception(f"Failed to authenticate Google Calendar: {exc}")
            return False

    async def list_events(
        self,
        start: datetime,
        end: datetime,
        max_results: int = 100,
    ) -> List[CalendarEvent]:
        """List events from Google Calendar."""
        if not self.service:
            logger.error("Google Calendar service not initialized")
            return []

        try:
            events_result = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=start.isoformat() + "Z",
                    timeMax=end.isoformat() + "Z",
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])

            return [self._convert_to_calendar_event(event) for event in events]

        except Exception as exc:
            logger.exception(f"Failed to list Google Calendar events: {exc}")
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
        """Create a new event in Google Calendar."""
        if not self.service:
            logger.error("Google Calendar service not initialized")
            return None

        try:
            event_body: Dict[str, Any] = {
                "summary": title,
                "start": {
                    "dateTime": start.isoformat(),
                    "timeZone": "UTC",
                },
                "end": {
                    "dateTime": end.isoformat(),
                    "timeZone": "UTC",
                },
            }

            if description:
                event_body["description"] = description

            if location:
                event_body["location"] = location

            if attendees:
                event_body["attendees"] = [{"email": email} for email in attendees]

            if reminder_minutes is not None:
                event_body["reminders"] = {
                    "useDefault": False,
                    "overrides": [
                        {"method": "popup", "minutes": reminder_minutes},
                    ],
                }

            created_event = (
                self.service.events()
                .insert(calendarId="primary", body=event_body)
                .execute()
            )

            logger.info(f"Created Google Calendar event: {created_event.get('id')}")
            return self._convert_to_calendar_event(created_event)

        except Exception as exc:
            logger.exception(f"Failed to create Google Calendar event: {exc}")
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
        """Update an existing Google Calendar event."""
        if not self.service:
            logger.error("Google Calendar service not initialized")
            return None

        try:
            # First, get the existing event
            event = self.service.events().get(calendarId="primary", eventId=event_id).execute()

            # Update fields
            if title:
                event["summary"] = title
            if start:
                event["start"]["dateTime"] = start.isoformat()
            if end:
                event["end"]["dateTime"] = end.isoformat()
            if description:
                event["description"] = description
            if location:
                event["location"] = location
            if attendees:
                event["attendees"] = [{"email": email} for email in attendees]

            # Update the event
            updated_event = (
                self.service.events()
                .update(calendarId="primary", eventId=event_id, body=event)
                .execute()
            )

            logger.info(f"Updated Google Calendar event: {event_id}")
            return self._convert_to_calendar_event(updated_event)

        except Exception as exc:
            logger.exception(f"Failed to update Google Calendar event: {exc}")
            return None

    async def delete_event(self, event_id: str) -> bool:
        """Delete a Google Calendar event."""
        if not self.service:
            logger.error("Google Calendar service not initialized")
            return False

        try:
            self.service.events().delete(calendarId="primary", eventId=event_id).execute()
            logger.info(f"Deleted Google Calendar event: {event_id}")
            return True

        except Exception as exc:
            logger.exception(f"Failed to delete Google Calendar event: {exc}")
            return False

    async def get_event(self, event_id: str) -> Optional[CalendarEvent]:
        """Get a specific Google Calendar event."""
        if not self.service:
            logger.error("Google Calendar service not initialized")
            return None

        try:
            event = self.service.events().get(calendarId="primary", eventId=event_id).execute()
            return self._convert_to_calendar_event(event)

        except Exception as exc:
            logger.exception(f"Failed to get Google Calendar event: {exc}")
            return None

    async def search_events(
        self,
        query: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        max_results: int = 20,
    ) -> List[CalendarEvent]:
        """Search Google Calendar events."""
        if not self.service:
            logger.error("Google Calendar service not initialized")
            return []

        try:
            params: Dict[str, Any] = {
                "calendarId": "primary",
                "q": query,
                "maxResults": max_results,
                "singleEvents": True,
                "orderBy": "startTime",
            }

            if start:
                params["timeMin"] = start.isoformat() + "Z"
            if end:
                params["timeMax"] = end.isoformat() + "Z"

            events_result = self.service.events().list(**params).execute()
            events = events_result.get("items", [])

            return [self._convert_to_calendar_event(event) for event in events]

        except Exception as exc:
            logger.exception(f"Failed to search Google Calendar events: {exc}")
            return []

    def _convert_to_calendar_event(self, google_event: Dict[str, Any]) -> CalendarEvent:
        """Convert Google Calendar event to standard CalendarEvent format."""
        start_data = google_event.get("start", {})
        end_data = google_event.get("end", {})

        # Parse datetime
        start_str = start_data.get("dateTime") or start_data.get("date")
        end_str = end_data.get("dateTime") or end_data.get("date")

        return CalendarEvent(
            {
                "id": google_event.get("id"),
                "title": google_event.get("summary", ""),
                "description": google_event.get("description", ""),
                "start": start_str,
                "end": end_str,
                "location": google_event.get("location", ""),
                "attendees": [
                    attendee.get("email") for attendee in google_event.get("attendees", [])
                ],
                "organizer": google_event.get("organizer", {}).get("email"),
                "all_day": "date" in start_data,
                "provider": "google",
                "raw": google_event,
            }
        )


__all__ = ["GoogleCalendarProvider"]
