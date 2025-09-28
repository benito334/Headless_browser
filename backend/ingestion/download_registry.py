"""SQLite-backed registry of downloaded source items to prevent re-downloading.

Currently used by the Instagram pipeline but designed to be reusable for
future YouTube / PDF / ePub ingesters.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_REG_DB = Path(os.getenv("DATA_DIR", "./data")) / "download_registry.db"


def _get_conn() -> sqlite3.Connection:
    _REG_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_REG_DB)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS downloaded_posts (
            id TEXT PRIMARY KEY,
            source_type TEXT NOT NULL,
            original_url TEXT,
            file_path TEXT,
            downloaded_at TEXT
        );
        """
    )
    return conn


def is_downloaded(post_id: str) -> bool:
    """Return True if the given post/file ID has been recorded already."""
    with _get_conn() as conn:
        cur = conn.execute("SELECT 1 FROM downloaded_posts WHERE id=?", (post_id,))
        return cur.fetchone() is not None


def record_download(post_id: str, *, source_type: str, original_url: str, file_path: str) -> None:
    """Persist that a given post/file has been downloaded.

    Safe to call multiple times thanks to the PRIMARY KEY + INSERT OR IGNORE.
    """
    ts = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO downloaded_posts (id, source_type, original_url, file_path, downloaded_at)
            VALUES (?,?,?,?,?);
            """,
            (post_id, source_type, original_url, file_path, ts),
        )
        conn.commit()
