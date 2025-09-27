"""FastAPI routes for backend API."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from backend.db.db import fetch_metadata

router = APIRouter()


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
