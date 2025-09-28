"""Main FastAPI application entrypoint with scheduler integration and static files."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.core.settings import Settings
from backend.core import automation
from datetime import datetime
import os, pathlib

from backend.api.routes import router as api_router
from backend.ingestion.logger_setup import init_logger

init_logger()
app = FastAPI(title="Headless Browser API", version="1.0.0")

# start automation if target_account configured
if Settings.target_account():
    automation.start()
# ---------------- Static files -----------------
DATA_DIR = os.getenv("DATA_DIR", "./data")
pathlib.Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=DATA_DIR), name="static")

# ---------------------------------------------------------------------------
# Routers & simple health endpoint
# ---------------------------------------------------------------------------
app.include_router(api_router, prefix="/api")

@app.get("/api/health")
async def health():
    return {"status": "ok"}
