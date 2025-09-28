# backend/api/routes.py
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
import asyncio
import pathlib, json
from datetime import datetime
from typing import Optional, List

from backend.ingestion.scheduler.async_bridge import async_scrape
from backend.ingestion.metadata.metadata_utils import insert_metadata_to_db
from backend.config import MAX_NEW_VIDEOS_PER_RUN

router = APIRouter()
LOG_DIR = pathlib.Path("logs"); LOG_DIR.mkdir(exist_ok=True)

# Simple in-process lock to prevent overlapping scrapes for the same user
_scrape_locks = {}

def _get_lock(username: str) -> asyncio.Lock:
    lock = _scrape_locks.get(username)
    if lock is None:
        lock = asyncio.Lock()
        _scrape_locks[username] = lock
    return lock

async def _run_scrape(username: str, max_downloads: int):
    lock = _get_lock(username)
    if lock.locked():
        # Another run in-progress; just log and return
        return
    async with lock:
        started = datetime.utcnow().isoformat()
        posts = await async_scrape(username, max_downloads)
        for p in posts:
            insert_metadata_to_db(p)
        finished = datetime.utcnow().isoformat()
        summary = {
            "status": "success",
            "downloaded": len(posts),
            "started": started,
            "finished": finished,
        }
        run_file = LOG_DIR / f"{username}_{int(datetime.utcnow().timestamp())}.json"
        run_file.write_text(json.dumps(summary, indent=2))

@router.post("/ingest/instagram/{username}")
async def ingest_now(
    username: str,
    bg: BackgroundTasks,
    max_downloads: int = Query(None, ge=0, description="Override MAX_NEW_VIDEOS_PER_RUN"),
):
    # Pick a safe test default when not provided
    md = max_downloads if max_downloads is not None else MAX_NEW_VIDEOS_PER_RUN
    bg.add_task(_run_scrape, username, md)
    return {"status": "accepted", "username": username, "max_downloads": md}
