"""Main FastAPI application entrypoint with scheduler integration and static files."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import os, pathlib

from backend.api.routes import router as api_router
from backend.ingestion.scheduler.scheduler_app import scrape_job
from backend.config import SCRAPE_INTERVAL, TARGET_ACCOUNT
from backend.ingestion.logger_setup import init_logger

app = FastAPI(title="Headless Browser API", version="1.0.0")

if TARGET_ACCOUNT:
    scheduler.add_job(scrape_job, "interval", minutes=SCRAPE_INTERVAL, max_instances=1, coalesce=True)
    scheduler.start()
else:
    # just log that scheduler is disabled
    from loguru import logger
    logger.warning("TARGET_ACCOUNT not set; scheduler disabled. Endpoint-only mode.")
# ---------------------------------------------------------------------------
# Static files mount  /static  ->  DATA_DIR
# ---------------------------------------------------------------------------
DATA_DIR = os.getenv("DATA_DIR", "./data")
pathlib.Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=DATA_DIR), name="static")

# ---------------------------------------------------------------------------
# Background scheduler (runs inside event loop)
# ---------------------------------------------------------------------------
scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def _startup():
    scheduler.add_job(scrape_job, "interval", minutes=SCRAPE_INTERVAL, next_run_time=datetime.utcnow())
    scheduler.start()

@app.on_event("shutdown")
async def _shutdown():
    scheduler.shutdown(wait=False)

# ---------------------------------------------------------------------------
# Routers & simple health endpoint
# ---------------------------------------------------------------------------
app.include_router(api_router, prefix="/api")

@app.get("/api/health")
async def health():
    return {"status": "ok"}
