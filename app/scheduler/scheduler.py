"""
APScheduler-based scheduler service for Jenny.

This module provides the core scheduling infrastructure using APScheduler with Redis backend.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
SCHEDULER_TIMEZONE = os.getenv("SCHEDULER_TIMEZONE", "UTC")

# Scheduler instance (singleton)
_scheduler: Optional[Any] = None

# Flag for APScheduler availability
APSCHEDULER_AVAILABLE = False

try:
    from apscheduler.executors.pool import ThreadPoolExecutor
    from apscheduler.jobstores.redis import RedisJobStore
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    APSCHEDULER_AVAILABLE = True
    logger.info("APScheduler library loaded successfully")
except ImportError:
    logger.warning("APScheduler not available. Install with: pip install apscheduler")


def get_scheduler() -> Optional[Any]:
    """
    Get or create the APScheduler instance.

    Returns:
        AsyncIOScheduler instance or None if not available
    """
    global _scheduler

    if not APSCHEDULER_AVAILABLE:
        logger.error("APScheduler not available")
        return None

    if _scheduler is not None:
        return _scheduler

    try:
        # Configure job stores
        jobstores = {
            "default": RedisJobStore(
                jobs_key="jenny:apscheduler:jobs",
                run_times_key="jenny:apscheduler:run_times",
                host=REDIS_URL.replace("redis://", "").split(":")[0],
                port=int(REDIS_URL.split(":")[-1]) if ":" in REDIS_URL else 6379,
            )
        }

        # Configure executors
        executors = {
            "default": ThreadPoolExecutor(max_workers=20),
        }

        # Job defaults
        job_defaults = {
            "coalesce": False,  # Don't combine multiple missed runs
            "max_instances": 3,  # Max concurrent instances of same job
            "misfire_grace_time": 60,  # Allow 1 minute grace for missed jobs
        }

        # Create scheduler
        _scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=SCHEDULER_TIMEZONE,
        )

        logger.info("APScheduler initialized successfully")
        return _scheduler

    except Exception as exc:
        logger.exception(f"Failed to initialize APScheduler: {exc}")
        return None


def start_scheduler() -> bool:
    """
    Start the scheduler.

    Returns:
        True if started successfully
    """
    scheduler = get_scheduler()

    if not scheduler:
        logger.error("Cannot start scheduler - not initialized")
        return False

    try:
        if not scheduler.running:
            scheduler.start()
            logger.info("Scheduler started successfully")
        else:
            logger.info("Scheduler already running")
        return True

    except Exception as exc:
        logger.exception(f"Failed to start scheduler: {exc}")
        return False


def stop_scheduler() -> bool:
    """
    Stop the scheduler.

    Returns:
        True if stopped successfully
    """
    global _scheduler

    if not _scheduler:
        logger.info("Scheduler not initialized, nothing to stop")
        return True

    try:
        if _scheduler.running:
            _scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped successfully")
        _scheduler = None
        return True

    except Exception as exc:
        logger.exception(f"Failed to stop scheduler: {exc}")
        return False


# Import Any for type hints
from typing import Any

__all__ = ["get_scheduler", "start_scheduler", "stop_scheduler"]
