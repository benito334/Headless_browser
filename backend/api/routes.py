"""FastAPI routes for backend API."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime
import json, pathlib, asyncio

from backend.db.db import fetch_metadata
from backend.ingestion.metadata.metadata_utils import insert_metadata_to_db
from backend.ingestion.scheduler.async_bridge import async_scrape
from backend.ingestion.instagram_ingestion.instagram_scraper import scrape_account_async
from backend.config import MAX_NEW_VIDEOS_PER_RUN

router = APIRouter()
LOG_DIR = pathlib.Path("logs")
LOG_DIR.mkdir(exist_ok=True)


@router.get("/metadata")
async def get_metadata(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    source_type: Optional[str] = Query(None, description="Filter by source type e.g. 'instagram'")
):
    try:
        records: List[dict] = fetch_metadata(limit=limit, offset=offset, source_type=source_type)
        return {
            "status": "success",
            "count": len(records),
            "records": records,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test_ingest/{username}")
async def test_ingest(username: str):
    """Temporary endpoint to trigger a one-off scrape using async wrapper."""
    posts = await scrape_account_async(username, True, MAX_NEW_VIDEOS_PER_RUN)
    return {"status": "success", "records": posts}


@router.post("/ingest/instagram/{username}")
async def ingest_now(username: str):
    started = datetime.utcnow().isoformat()
    try:
        posts = await async_scrape(username, MAX_NEW_VIDEOS_PER_RUN)
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
        return summary
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/logs/instagram/{username}")
async def get_ingest_logs(username: str):
    files = sorted(LOG_DIR.glob(f"{username}_*.json"))
    return [json.loads(f.read_text()) for f in files]
