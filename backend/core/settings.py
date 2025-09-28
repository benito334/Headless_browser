"""Runtime-modifiable settings persisted in SQLite.
Initial values are seeded from environment variables (i.e. .env) on first use.
"""
from __future__ import annotations
import os, sqlite3
from pathlib import Path
from typing import Any, Dict

_DB = Path(os.getenv("DATA_DIR", "./data")) / "settings.db"

_DEFAULTS: Dict[str, Any] = {
    "SCRAPE_INTERVAL": os.getenv("SCRAPE_INTERVAL", "30"),
    "MAX_NEW_VIDEOS_PER_RUN": os.getenv("MAX_NEW_VIDEOS_PER_RUN", "4"),
    "WAIT_MIN_SECONDS": os.getenv("WAIT_MIN_SECONDS", "60"),
    "WAIT_MAX_SECONDS": os.getenv("WAIT_MAX_SECONDS", "120"),
    "TARGET_ACCOUNT": os.getenv("TARGET_ACCOUNT", ""),
}


def _ensure():
    _DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB)
    conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);")
    # seed missing defaults
    for k, v in _DEFAULTS.items():
        conn.execute("INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?);", (k, str(v)))
    conn.commit()
    return conn


class Settings:
    """Dictionary-like access to persisted settings."""

    @classmethod
    def get(cls, key: str) -> str:
        with _ensure() as conn:
            cur = conn.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = cur.fetchone()
            if row:
                return row[0]
            raise KeyError(key)

    @classmethod
    def set(cls, key: str, value: str):
        with _ensure() as conn:
            conn.execute("INSERT OR REPLACE INTO settings(key, value) VALUES (?, ?);", (key, str(value)))
            conn.commit()

    # typed helpers ---------------------------------------------------------
    @classmethod
    def scrape_interval(cls) -> int:
        return int(cls.get("SCRAPE_INTERVAL"))

    @classmethod
    def max_downloads(cls) -> int:
        return int(cls.get("MAX_NEW_VIDEOS_PER_RUN"))

    @classmethod
    def wait_bounds(cls) -> tuple[float, float]:
        return float(cls.get("WAIT_MIN_SECONDS")), float(cls.get("WAIT_MAX_SECONDS"))

    @classmethod
    def target_account(cls) -> str:
        return cls.get("TARGET_ACCOUNT")
