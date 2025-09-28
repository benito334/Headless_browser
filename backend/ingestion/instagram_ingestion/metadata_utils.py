"""Lightweight metadata helpers (Instagram-only for now)."""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

ISO_8601 = "%Y-%m-%dT%H:%M:%SZ"

def _now_iso() -> str:
    return datetime.utcnow().replace(tzinfo=timezone.utc).strftime(ISO_8601)

def build_metadata(*, original_url: str, file_path: str, author: str | None = None, publish_date: str | None = None, notes: str | None = None) -> Dict[str, Any]:
    return {
        "source_type": "instagram",
        "original_url": original_url,
        "file_path": file_path,
        "author": author,
        "publish_date": publish_date,
        "length_seconds": None,  # duration omitted
        "language": "und",
        "ingest_date": _now_iso(),
        "notes": notes,
    }

def write_sidecar(meta: Dict[str, Any]) -> Path:
    fp = Path(meta["file_path"])
    sidecar = fp.with_suffix('.json')
    sidecar.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding='utf-8')
    return sidecar
