"""Utility helpers for constructing and writing metadata side-car files
for downloaded Instagram media.

This module purposefully lives inside the `instagram_ingestion` package so that
relative imports (`from .metadata_utils import …`) work regardless of whether
it is executed inside the container or directly on the host.
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from loguru import logger

ISO_8601_FORMAT = "%Y-%m-%dT%H:%M:%SZ"  # always UTC with trailing Z


def _iso_now() -> str:
    """Return current UTC time formatted as ISO-8601."""
    return datetime.utcnow().replace(tzinfo=timezone.utc).strftime(ISO_8601_FORMAT)


def _normalize_iso8601(dt: str | datetime | None) -> str | None:
    """Convert various datetime inputs to UTC ISO-8601, or None.

    Accepts either a datetime instance or a string assumed to already be
    ISO-formatted.  Returned string always ends with Z (UTC).
    """
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.astimezone(timezone.utc).strftime(ISO_8601_FORMAT)
    # assume string already ISO; ensure trailing Z
    if dt.endswith("Z"):
        return dt
    return dt + "Z"


def build_metadata(*,
                   original_url: str,
                   file_path: str,
                   author: str,
                   publish_date: str | datetime | None = None,
                   length_seconds: int | None = None,
                   language: str | None = None,
                   license_: str | None = None,
                   notes: str | None = None) -> Dict[str, Any]:
    """Assemble a metadata dictionary according to ingest schema."""
    metadata: Dict[str, Any] = {
        "source_id": str(uuid.uuid4()),
        "source_type": "instagram",
        "original_url": original_url,
        "file_path": file_path,
        "publish_date": _normalize_iso8601(publish_date),
        "author": [author] if author else [],
        "length_seconds": length_seconds,
        "language": language,
        "license": license_,
        "ingest_date": _iso_now(),
        "notes": notes,
    }
    return metadata


def insert_metadata_to_db(metadata: Dict[str, Any], db_path: str = "backend/db/content.db") -> None:
    """Insert or ignore metadata row into SQLite for easy querying/dedupe."""
    import sqlite3

    # Ensure parent directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = None
    try:
        conn = sqlite3.connect(db_path)
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
        logger.exception("Failed to insert metadata into DB %s", db_path)
        # swallow error to avoid crashing caller
    finally:
        if conn:
            conn.close()


def write_sidecar(metadata: Dict[str, Any]) -> Path:
    """Write the metadata JSON next to the media file.

    Returns the Path to the written JSON.
    """
    media_path = Path(metadata["file_path"])
    sidecar_path = media_path.with_suffix(".json")
    try:
        sidecar_path.parent.mkdir(parents=True, exist_ok=True)
        sidecar_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        logger.exception("Failed to write metadata sidecar for {}", media_path)
        raise
    return sidecar_path
