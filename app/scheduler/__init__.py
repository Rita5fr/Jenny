"""
Scheduler package for Jenny AI Assistant.

This package provides scheduled reminders, recurring tasks, and background jobs using APScheduler.

Features:
- One-time reminders
- Recurring reminders (daily, weekly, monthly)
- Cron-based scheduling
- Background job execution
- Redis-backed job store for persistence

Usage:
    from app.scheduler import get_scheduler, schedule_reminder

    scheduler = get_scheduler()
    scheduler.start()

    # Schedule a reminder
    job_id = await schedule_reminder(
        user_id="user_123",
        message="Take medication",
        run_at=datetime.now() + timedelta(hours=1)
    )
"""

from app.scheduler.reminder_service import (
    cancel_reminder,
    list_reminders,
    schedule_recurring_reminder,
    schedule_reminder,
)
from app.scheduler.scheduler import get_scheduler, start_scheduler, stop_scheduler

__all__ = [
    "get_scheduler",
    "start_scheduler",
    "stop_scheduler",
    "schedule_reminder",
    "schedule_recurring_reminder",
    "cancel_reminder",
    "list_reminders",
]
