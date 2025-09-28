"""API routes: metadata (placeholder), settings management, automation control."""
from fastapi import APIRouter, HTTPException, Body
from backend.core.settings import Settings
from backend.core import automation
from typing import Dict

router = APIRouter()

# ---------------- Settings Endpoints -----------------
@router.get("/settings", response_model=Dict[str, str])
async def get_settings():
    """Return all persisted settings."""
    return {
        "SCRAPE_INTERVAL": str(Settings.scrape_interval()),
        "MAX_NEW_VIDEOS_PER_RUN": str(Settings.max_downloads()),
        "WAIT_MIN_SECONDS": str(Settings.wait_bounds()[0]),
        "WAIT_MAX_SECONDS": str(Settings.wait_bounds()[1]),
        "TARGET_ACCOUNT": Settings.target_account(),
    }


@router.put("/settings/{key}")
async def update_setting(key: str, value: str = Body(..., embed=True)):
    valid_keys = {
        "SCRAPE_INTERVAL",
        "MAX_NEW_VIDEOS_PER_RUN",
        "WAIT_MIN_SECONDS",
        "WAIT_MAX_SECONDS",
        "TARGET_ACCOUNT",
    }
    if key not in valid_keys:
        raise HTTPException(400, f"Unsupported setting {key}")
    Settings.set(key, value)

    # apply side-effects
    if key == "SCRAPE_INTERVAL":
        automation.reschedule(int(value))
    return {"status": "updated", key: value}


# ---------------- Automation control -----------------
@router.post("/automation/start")
async def start_automation():
    automation.start()
    return {"status": "started"}


@router.post("/automation/stop")
async def stop_automation():
    automation.stop()
    return {"status": "stopped"}


@router.post("/automation/interval/{minutes}")
async def change_interval(minutes: int):
    Settings.set("SCRAPE_INTERVAL", str(minutes))
    automation.reschedule(minutes)
    return {"status": "rescheduled", "minutes": minutes}
