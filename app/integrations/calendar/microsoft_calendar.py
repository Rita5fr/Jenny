"""
Microsoft Outlook Calendar integration.

This module provides integration with Microsoft Graph API for Outlook/Office 365 calendars.

Setup:
    1. Register app in Azure AD (Azure Active Directory)
    2. Configure redirect URI
    3. Get application (client) ID and client secret
    4. Set environment variables:
        - MICROSOFT_CLIENT_ID
        - MICROSOFT_CLIENT_SECRET
        - MICROSOFT_REDIRECT_URI

Usage:
    from app.integrations.calendar.microsoft_calendar import MicrosoftCalendarProvider

    calendar = MicrosoftCalendarProvider(user_id="user_123")
    auth_url = calendar.get_authorization_url()
    # User visits auth_url and gets code
    await calendar.authenticate(auth_code="...")
    events = await calendar.list_events(start=datetime.now(), end=datetime.now() + timedelta(days=7))
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

from app.integrations.calendar.base import CalendarEvent

logger = logging.getLogger(__name__)

load_dotenv()

# Microsoft Graph API configuration
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
MICROSOFT_REDIRECT_URI = os.getenv("MICROSOFT_REDIRECT_URI", "http://localhost:8044/auth/microsoft/callback")

AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES = ["Calendars.ReadWrite", "Calendars.Read"]
GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"

# Flag for MSAL availability
MSAL_AVAILABLE = False

try:
    import msal

    MSAL_AVAILABLE = True
    logger.info("Microsoft MSAL library loaded successfully")
except ImportError:
    logger.warning("Microsoft MSAL not available. Install with: pip install msal")


class MicrosoftCalendarProvider:
    """Microsoft Outlook/Office 365 Calendar provider implementation."""

    def __init__(self, user_id: str):
        """
        Initialize Microsoft Calendar provider.

        Args:
            user_id: User identifier (used to store/retrieve credentials)
        """
        self.user_id = user_id
        self.access_token = None
        self.msal_app = None

        if MSAL_AVAILABLE:
            self.msal_app = msal.PublicClientApplication(
                MICROSOFT_CLIENT_ID,
                authority=AUTHORITY,
            )

    def get_authorization_url(self) -> str:
        """
        Get the authorization URL for OAuth 2.0 flow.

        Returns:
            Authorization URL for user to visit
        """
        if not MSAL_AVAILABLE:
            raise RuntimeError("Microsoft MSAL library not available")

        if not self.msal_app:
            raise RuntimeError("MSAL app not initialized")

        auth_url = self.msal_app.get_authorization_request_url(
            scopes=SCOPES,
            redirect_uri=MICROSOFT_REDIRECT_URI,
        )

        return auth_url

    async def authenticate(self, auth_code: str) -> bool:
        """
        Authenticate using authorization code from OAuth flow.

        Args:
            auth_code: Authorization code from OAuth callback

        Returns:
            True if authentication successful
        """
        if not MSAL_AVAILABLE or not self.msal_app:
            raise RuntimeError("Microsoft MSAL library not available")

        try:
            result = self.msal_app.acquire_token_by_authorization_code(
                code=auth_code,
                scopes=SCOPES,
                redirect_uri=MICROSOFT_REDIRECT_URI,
            )

            if "access_token" in result:
                self.access_token = result["access_token"]
                # TODO: Store refresh token securely for this user
                logger.info(f"Microsoft Calendar authenticated for user {self.user_id}")
                return True
            else:
                logger.error(f"Failed to get access token: {result.get('error_description')}")
                return False

        except Exception as exc:
            logger.exception(f"Failed to authenticate Microsoft Calendar: {exc}")
            return False

    async def _make_graph_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Make a request to Microsoft Graph API.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (e.g., "/me/events")
            json_data: JSON body for POST/PATCH requests
            params: Query parameters

        Returns:
            Response JSON or None if error
        """
        if not self.access_token:
            logger.error("Not authenticated - no access token")
            return None

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        url = f"{GRAPH_API_ENDPOINT}{endpoint}"

        async with httpx.AsyncClient() as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=json_data)
                elif method.upper() == "PATCH":
                    response = await client.patch(url, headers=headers, json=json_data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    logger.error(f"Unsupported HTTP method: {method}")
                    return None

                response.raise_for_status()
                return response.json() if method.upper() != "DELETE" else {}

            except httpx.HTTPStatusError as exc:
                logger.error(f"Graph API request failed: {exc.response.status_code} - {exc.response.text}")
                return None
            except Exception as exc:
                logger.exception(f"Failed to make Graph API request: {exc}")
                return None

    async def list_events(
        self,
        start: datetime,
        end: datetime,
        max_results: int = 100,
    ) -> List[CalendarEvent]:
        """List events from Microsoft Calendar."""
        params = {
            "$top": max_results,
            "$orderby": "start/dateTime",
            "$filter": f"start/dateTime ge '{start.isoformat()}' and end/dateTime le '{end.isoformat()}'",
        }

        result = await self._make_graph_request("GET", "/me/events", params=params)

        if not result:
            return []

        events = result.get("value", [])
        return [self._convert_to_calendar_event(event) for event in events]

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
        """Create a new event in Microsoft Calendar."""
        event_body: Dict[str, Any] = {
            "subject": title,
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
            event_body["body"] = {
                "contentType": "text",
                "content": description,
            }

        if location:
            event_body["location"] = {"displayName": location}

        if attendees:
            event_body["attendees"] = [
                {
                    "emailAddress": {"address": email},
                    "type": "required",
                }
                for email in attendees
            ]

        if reminder_minutes is not None:
            event_body["isReminderOn"] = True
            event_body["reminderMinutesBeforeStart"] = reminder_minutes

        result = await self._make_graph_request("POST", "/me/events", json_data=event_body)

        if result:
            logger.info(f"Created Microsoft Calendar event: {result.get('id')}")
            return self._convert_to_calendar_event(result)

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
        """Update an existing Microsoft Calendar event."""
        event_body: Dict[str, Any] = {}

        if title:
            event_body["subject"] = title
        if start:
            event_body["start"] = {
                "dateTime": start.isoformat(),
                "timeZone": "UTC",
            }
        if end:
            event_body["end"] = {
                "dateTime": end.isoformat(),
                "timeZone": "UTC",
            }
        if description:
            event_body["body"] = {
                "contentType": "text",
                "content": description,
            }
        if location:
            event_body["location"] = {"displayName": location}
        if attendees:
            event_body["attendees"] = [
                {
                    "emailAddress": {"address": email},
                    "type": "required",
                }
                for email in attendees
            ]

        result = await self._make_graph_request("PATCH", f"/me/events/{event_id}", json_data=event_body)

        if result:
            logger.info(f"Updated Microsoft Calendar event: {event_id}")
            return self._convert_to_calendar_event(result)

        return None

    async def delete_event(self, event_id: str) -> bool:
        """Delete a Microsoft Calendar event."""
        result = await self._make_graph_request("DELETE", f"/me/events/{event_id}")
        if result is not None:
            logger.info(f"Deleted Microsoft Calendar event: {event_id}")
            return True
        return False

    async def get_event(self, event_id: str) -> Optional[CalendarEvent]:
        """Get a specific Microsoft Calendar event."""
        result = await self._make_graph_request("GET", f"/me/events/{event_id}")
        if result:
            return self._convert_to_calendar_event(result)
        return None

    async def search_events(
        self,
        query: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        max_results: int = 20,
    ) -> List[CalendarEvent]:
        """Search Microsoft Calendar events."""
        params = {
            "$search": f'"{query}"',
            "$top": max_results,
        }

        if start and end:
            params["$filter"] = f"start/dateTime ge '{start.isoformat()}' and end/dateTime le '{end.isoformat()}'"

        result = await self._make_graph_request("GET", "/me/events", params=params)

        if not result:
            return []

        events = result.get("value", [])
        return [self._convert_to_calendar_event(event) for event in events]

    def _convert_to_calendar_event(self, ms_event: Dict[str, Any]) -> CalendarEvent:
        """Convert Microsoft Graph event to standard CalendarEvent format."""
        start_data = ms_event.get("start", {})
        end_data = ms_event.get("end", {})

        attendees = []
        for attendee in ms_event.get("attendees", []):
            email_data = attendee.get("emailAddress", {})
            if email_data.get("address"):
                attendees.append(email_data["address"])

        return CalendarEvent(
            {
                "id": ms_event.get("id"),
                "title": ms_event.get("subject", ""),
                "description": ms_event.get("body", {}).get("content", ""),
                "start": start_data.get("dateTime"),
                "end": end_data.get("dateTime"),
                "location": ms_event.get("location", {}).get("displayName", ""),
                "attendees": attendees,
                "organizer": ms_event.get("organizer", {}).get("emailAddress", {}).get("address"),
                "all_day": ms_event.get("isAllDay", False),
                "provider": "microsoft",
                "raw": ms_event,
            }
        )


__all__ = ["MicrosoftCalendarProvider"]
