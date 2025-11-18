"""
Reminder service for scheduling and managing user reminders.

This module provides functions to schedule, list, and cancel reminders.
Reminders can be sent via Telegram, WhatsApp, or other notification channels.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.scheduler.scheduler import get_scheduler

logger = logging.getLogger(__name__)


async def send_reminder_notification(
    user_id: str,
    message: str,
    reminder_id: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Send a reminder notification to the user.

    This function is called by the scheduler when a reminder is due.

    Args:
        user_id: User identifier
        message: Reminder message
        reminder_id: Unique reminder ID
        metadata: Optional metadata (notification channel, etc.)
    """
    logger.info(f"Sending reminder {reminder_id} to user {user_id}: {message}")

    try:
        # Determine notification channel
        channel = metadata.get("channel", "telegram") if metadata else "telegram"

        if channel == "telegram":
            await _send_telegram_reminder(user_id, message)
        elif channel == "whatsapp":
            await _send_whatsapp_reminder(user_id, message)
        else:
            logger.warning(f"Unknown notification channel: {channel}")

        # Log successful delivery
        logger.info(f"Reminder {reminder_id} delivered successfully")

    except Exception as exc:
        logger.exception(f"Failed to send reminder {reminder_id}: {exc}")


async def _send_telegram_reminder(user_id: str, message: str) -> None:
    """Send reminder via Telegram."""
    try:
        # Import Telegram bot here to avoid circular imports
        from app.integrations.telegram.bot import send_message

        await send_message(user_id=user_id, text=f"🔔 Reminder: {message}")
    except Exception as exc:
        logger.warning(f"Failed to send Telegram reminder: {exc}")


async def _send_whatsapp_reminder(user_id: str, message: str) -> None:
    """Send reminder via WhatsApp."""
    try:
        # Import WhatsApp client here to avoid circular imports
        from app.integrations.whatsapp.client import send_message

        await send_message(user_id=user_id, text=f"🔔 Reminder: {message}")
    except Exception as exc:
        logger.warning(f"Failed to send WhatsApp reminder: {exc}")


async def schedule_reminder(
    user_id: str,
    message: str,
    run_at: datetime,
    channel: str = "telegram",
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Schedule a one-time reminder.

    Args:
        user_id: User identifier
        message: Reminder message
        run_at: When to send the reminder
        channel: Notification channel (telegram, whatsapp)
        metadata: Optional metadata

    Returns:
        Job ID for the scheduled reminder

    Example:
        job_id = await schedule_reminder(
            user_id="user_123",
            message="Take medication",
            run_at=datetime.now() + timedelta(hours=1),
            channel="telegram"
        )
    """
    scheduler = get_scheduler()
    if not scheduler:
        raise RuntimeError("Scheduler not available")

    # Generate unique job ID
    job_id = f"reminder_{user_id}_{uuid.uuid4().hex[:8]}"

    # Prepare metadata
    job_metadata = metadata or {}
    job_metadata["channel"] = channel
    job_metadata["user_id"] = user_id

    try:
        # Schedule the job
        scheduler.add_job(
            send_reminder_notification,
            "date",  # One-time job
            run_date=run_at,
            args=[user_id, message, job_id, job_metadata],
            id=job_id,
            replace_existing=False,
        )

        logger.info(f"Scheduled reminder {job_id} for {user_id} at {run_at}")
        return job_id

    except Exception as exc:
        logger.exception(f"Failed to schedule reminder: {exc}")
        raise RuntimeError(f"Failed to schedule reminder: {exc}") from exc


async def schedule_recurring_reminder(
    user_id: str,
    message: str,
    cron_expression: Optional[str] = None,
    interval_minutes: Optional[int] = None,
    hour: Optional[int] = None,
    minute: Optional[int] = None,
    day_of_week: Optional[str] = None,
    channel: str = "telegram",
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Schedule a recurring reminder.

    Args:
        user_id: User identifier
        message: Reminder message
        cron_expression: Cron expression (if provided, overrides other params)
        interval_minutes: Repeat every X minutes
        hour: Hour of day (0-23, for daily reminders)
        minute: Minute of hour (0-59)
        day_of_week: Day of week (mon, tue, wed, thu, fri, sat, sun)
        channel: Notification channel
        metadata: Optional metadata

    Returns:
        Job ID for the scheduled reminder

    Examples:
        # Daily at 9 AM
        await schedule_recurring_reminder(
            user_id="user_123",
            message="Morning standup",
            hour=9,
            minute=0
        )

        # Every Monday at 10 AM
        await schedule_recurring_reminder(
            user_id="user_123",
            message="Weekly review",
            day_of_week="mon",
            hour=10,
            minute=0
        )

        # Every 30 minutes
        await schedule_recurring_reminder(
            user_id="user_123",
            message="Drink water",
            interval_minutes=30
        )
    """
    scheduler = get_scheduler()
    if not scheduler:
        raise RuntimeError("Scheduler not available")

    # Generate unique job ID
    job_id = f"recurring_reminder_{user_id}_{uuid.uuid4().hex[:8]}"

    # Prepare metadata
    job_metadata = metadata or {}
    job_metadata["channel"] = channel
    job_metadata["user_id"] = user_id
    job_metadata["recurring"] = True

    try:
        if cron_expression:
            # Use cron trigger
            scheduler.add_job(
                send_reminder_notification,
                "cron",
                **_parse_cron_expression(cron_expression),
                args=[user_id, message, job_id, job_metadata],
                id=job_id,
                replace_existing=False,
            )
        elif interval_minutes:
            # Use interval trigger
            scheduler.add_job(
                send_reminder_notification,
                "interval",
                minutes=interval_minutes,
                args=[user_id, message, job_id, job_metadata],
                id=job_id,
                replace_existing=False,
            )
        else:
            # Use cron trigger with specific time
            cron_kwargs = {}
            if day_of_week:
                cron_kwargs["day_of_week"] = day_of_week
            if hour is not None:
                cron_kwargs["hour"] = hour
            if minute is not None:
                cron_kwargs["minute"] = minute

            scheduler.add_job(
                send_reminder_notification,
                "cron",
                **cron_kwargs,
                args=[user_id, message, job_id, job_metadata],
                id=job_id,
                replace_existing=False,
            )

        logger.info(f"Scheduled recurring reminder {job_id} for {user_id}")
        return job_id

    except Exception as exc:
        logger.exception(f"Failed to schedule recurring reminder: {exc}")
        raise RuntimeError(f"Failed to schedule recurring reminder: {exc}") from exc


def _parse_cron_expression(cron_expr: str) -> Dict[str, Any]:
    """Parse cron expression into APScheduler kwargs."""
    parts = cron_expr.split()
    if len(parts) != 5:
        raise ValueError("Invalid cron expression. Expected format: 'minute hour day month day_of_week'")

    return {
        "minute": parts[0],
        "hour": parts[1],
        "day": parts[2],
        "month": parts[3],
        "day_of_week": parts[4],
    }


async def cancel_reminder(job_id: str) -> bool:
    """
    Cancel a scheduled reminder.

    Args:
        job_id: Job ID to cancel

    Returns:
        True if cancelled successfully
    """
    scheduler = get_scheduler()
    if not scheduler:
        logger.error("Scheduler not available")
        return False

    try:
        scheduler.remove_job(job_id)
        logger.info(f"Cancelled reminder {job_id}")
        return True

    except Exception as exc:
        logger.warning(f"Failed to cancel reminder {job_id}: {exc}")
        return False


async def list_reminders(user_id: str) -> List[Dict[str, Any]]:
    """
    List all scheduled reminders for a user.

    Args:
        user_id: User identifier

    Returns:
        List of reminder dictionaries
    """
    scheduler = get_scheduler()
    if not scheduler:
        logger.error("Scheduler not available")
        return []

    try:
        all_jobs = scheduler.get_jobs()
        user_reminders = []

        for job in all_jobs:
            # Check if this job belongs to the user
            if job.id.startswith(f"reminder_{user_id}_") or job.id.startswith(
                f"recurring_reminder_{user_id}_"
            ):
                user_reminders.append(
                    {
                        "id": job.id,
                        "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                        "recurring": job.id.startswith("recurring_reminder_"),
                        "trigger": str(job.trigger),
                    }
                )

        logger.debug(f"Found {len(user_reminders)} reminders for user {user_id}")
        return user_reminders

    except Exception as exc:
        logger.exception(f"Failed to list reminders: {exc}")
        return []


__all__ = [
    "schedule_reminder",
    "schedule_recurring_reminder",
    "cancel_reminder",
    "list_reminders",
    "send_reminder_notification",
]
