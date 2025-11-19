"""Calendar OAuth and management API endpoints."""
from __future__ import annotations

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.services.calendar_auth import (
    save_calendar_token,
    delete_calendar_token,
    list_connected_calendars,
    is_calendar_connected,
)
from app.integrations.calendar.google_calendar import GoogleCalendarProvider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar", tags=["calendar"])


class ConnectCalendarResponse(BaseModel):
    """Response for calendar connection request."""
    provider: str
    authorization_url: str
    message: str


class CalendarStatusResponse(BaseModel):
    """Response for calendar status."""
    connected_calendars: list[Dict[str, Any]]
    available_providers: list[str]


@router.get("/connect/{provider}")
async def connect_calendar(
    provider: str,
    user_id: str = Query(..., description="User ID to connect calendar for"),
) -> ConnectCalendarResponse:
    """
    Generate OAuth authorization URL for connecting a calendar.

    User should visit this URL to authorize Jenny to access their calendar.

    Args:
        provider: Calendar provider (google, microsoft, apple)
        user_id: User identifier

    Returns:
        Authorization URL to visit
    """
    # Check if already connected
    if await is_calendar_connected(user_id, provider):
        return ConnectCalendarResponse(
            provider=provider,
            authorization_url="",
            message=f"{provider.title()} Calendar is already connected! To reconnect, disconnect first.",
        )

    if provider == "google":
        try:
            calendar_provider = GoogleCalendarProvider(user_id=user_id)
            auth_url = calendar_provider.get_authorization_url()

            return ConnectCalendarResponse(
                provider=provider,
                authorization_url=auth_url,
                message=f"Click the link to connect your {provider.title()} Calendar",
            )
        except Exception as exc:
            logger.exception(f"Failed to generate Google Calendar auth URL: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate authorization URL: {str(exc)}",
            ) from exc

    elif provider == "microsoft":
        # TODO: Implement Microsoft OAuth
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Microsoft Calendar integration coming soon!",
        )

    elif provider == "apple":
        # TODO: Implement Apple Calendar (CalDAV)
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Apple Calendar integration coming soon!",
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported calendar provider: {provider}. Use: google, microsoft, or apple",
        )


@router.get("/auth/google/callback")
async def google_calendar_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(None, description="State parameter"),
    user_id: str = Query(..., description="User ID"),
) -> Dict[str, Any]:
    """
    Handle OAuth callback from Google Calendar.

    This endpoint is called by Google after user authorizes the app.

    Args:
        code: Authorization code from Google
        state: State parameter (optional)
        user_id: User identifier

    Returns:
        Success message
    """
    try:
        calendar_provider = GoogleCalendarProvider(user_id=user_id)

        # Exchange code for tokens
        success = await calendar_provider.authenticate(code)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to authenticate with Google Calendar",
            )

        # Save tokens to database
        # Get credentials from provider
        if calendar_provider.credentials:
            await save_calendar_token(
                user_id=user_id,
                provider="google",
                access_token=calendar_provider.credentials.token,
                refresh_token=calendar_provider.credentials.refresh_token,
                token_expiry=calendar_provider.credentials.expiry,
                token_data={
                    "scopes": calendar_provider.credentials.scopes,
                    "token_uri": calendar_provider.credentials.token_uri,
                },
            )

        logger.info(f"Google Calendar connected successfully for user {user_id}")

        return {
            "status": "success",
            "provider": "google",
            "message": "Google Calendar connected successfully! You can now create events.",
            "user_id": user_id,
        }

    except Exception as exc:
        logger.exception(f"Google Calendar callback failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete calendar connection: {str(exc)}",
        ) from exc


@router.post("/disconnect/{provider}")
async def disconnect_calendar(
    provider: str,
    user_id: str = Query(..., description="User ID"),
) -> Dict[str, str]:
    """
    Disconnect a calendar provider.

    Args:
        provider: Calendar provider to disconnect (google, microsoft, apple)
        user_id: User identifier

    Returns:
        Success message
    """
    if provider not in ["google", "microsoft", "apple"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider: {provider}. Use: google, microsoft, or apple",
        )

    # Check if connected
    if not await is_calendar_connected(user_id, provider):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{provider.title()} Calendar is not connected",
        )

    # Delete token
    success = await delete_calendar_token(user_id, provider)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect calendar",
        )

    return {
        "status": "success",
        "provider": provider,
        "message": f"{provider.title()} Calendar disconnected successfully",
    }


@router.get("/status")
async def get_calendar_status(
    user_id: str = Query(..., description="User ID"),
) -> CalendarStatusResponse:
    """
    Get calendar connection status for a user.

    Args:
        user_id: User identifier

    Returns:
        List of connected calendars and available providers
    """
    connected = await list_connected_calendars(user_id)

    return CalendarStatusResponse(
        connected_calendars=connected,
        available_providers=["google", "microsoft", "apple"],
    )


__all__ = ["router"]
