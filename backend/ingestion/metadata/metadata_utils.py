"""Generic metadata utilities usable by any ingestion source (instagram, youtube, pdf, etc.)."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from loguru import logger

ISO_8601 = "%Y-%m-%dT%H:%M:%SZ"


def _iso_now() -> str:
    return datetime.utcnow().replace(tzinfo=timezone.utc).strftime(ISO_8601)


def _normalize_iso(dt: str | datetime | None) -> str | None:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.astimezone(timezone.utc).strftime(ISO_8601)
    return dt if dt.endswith("Z") else dt + "Z"


def build_metadata(*,
                   source_type: str,
                   original_url: str,
                   file_path: str,
                   publish_date: str | datetime | None = None,
                   author: str | None = None,
                   length_seconds: int | None = None,
                   language: str | None = "und",
                   license_: str | None = None,
                   notes: str | None = None) -> Dict[str, Any]:
    """Return a dict following the canonical metadata schema."""
    return {
        "source_id": str(uuid.uuid4()),
        "source_type": source_type,
        "original_url": original_url,
        "file_path": file_path,
        "publish_date": _normalize_iso(publish_date),
        "author": [author] if author else [],
        "length_seconds": length_seconds,
        "language": language,
        "license": license_,
        "ingest_date": _iso_now(),
        "notes": notes,
    }


def write_sidecar(metadata: Dict[str, Any]) -> Path:
    media_path = Path(metadata["file_path"])
    sidecar_path = media_path.with_suffix(".json")
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    sidecar_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return sidecar_path


def insert_metadata_to_db(metadata: Dict[str, Any], db_path: str = "backend/db/content.db") -> None:
    import sqlite3
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ingested_content (
              id TEXT PRIMARY KEY,
              source_type TEXT NOT NULL,
              original_url TEXT NOT NULL,
              file_path TEXT NOT NULL,
              publish_date TEXT,
              author TEXT,
              length_seconds INTEGER,
              language TEXT,
              license TEXT,
              ingest_date TEXT NOT NULL,
              notes TEXT,
              UNIQUE(original_url, file_path) ON CONFLICT IGNORE
            );
            """
        )
        # indexes for faster lookup
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ingest_date ON ingested_content(ingest_date);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_source_type ON ingested_content(source_type);")

        conn.execute(
            """
            INSERT OR IGNORE INTO ingested_content (
              id, source_type, original_url, file_path, publish_date, author, length_seconds,
              language, license, ingest_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                metadata["source_id"],
                metadata["source_type"],
                metadata["original_url"],
                metadata["file_path"],
                metadata["publish_date"],
                ",".join(metadata.get("author", [])),
                metadata["length_seconds"],
                metadata["language"],
                metadata["license"],
                metadata["ingest_date"],
                metadata["notes"],
            ),
        )
        conn.commit()
    except Exception:
        logger.exception("Failed to insert metadata into DB")
    finally:
        conn.close()
