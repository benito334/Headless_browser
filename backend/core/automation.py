"""Wrapper around global APScheduler instance for start/stop/reschedule."""
from __future__ import annotations
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.ingestion.scheduler.scheduler_app import scrape_job
from backend.core.settings import Settings
from loguru import logger

scheduler = AsyncIOScheduler()
_JOB_ID = "instagram_scrape"


def start():
    if scheduler.get_job(_JOB_ID):
        return
    mins = Settings.scrape_interval()
    if mins <= 0:
        logger.warning("SCRAPE_INTERVAL <=0; not starting scheduler")
        return
    scheduler.add_job(scrape_job, "interval", minutes=mins, id=_JOB_ID, max_instances=1, coalesce=True)
    scheduler.start()
    logger.info("Scheduler started with interval {} minutes", mins)


def stop():
    job = scheduler.get_job(_JOB_ID)
    if job:
        job.remove()
        logger.info("Scheduler stopped")


def reschedule(minutes: int):
    job = scheduler.get_job(_JOB_ID)
    if job:
        scheduler.reschedule_job(_JOB_ID, trigger="interval", minutes=minutes)
        logger.info("Scheduler rescheduled to {} minutes", minutes)
    else:
        # if not running, start with new interval
        Settings.set("SCRAPE_INTERVAL", str(minutes))
        start()
