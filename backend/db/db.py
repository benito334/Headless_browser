import sqlite3
from pathlib import Path
from typing import Dict, List
from loguru import logger

from backend.config import DOWNLOAD_DIR

DB_PATH = Path(DOWNLOAD_DIR) / "instagram_posts.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS posts (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    date_posted TEXT,
    media_type TEXT
);
"""

def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db() -> None:
    conn = get_connection()
    with conn:
        conn.execute(CREATE_TABLE_SQL)
    logger.debug("Database initialized at {}", DB_PATH)

def get_seen_post_ids(conn: sqlite3.Connection) -> List[str]:
    cur = conn.execute("SELECT id FROM posts")
    return [row[0] for row in cur.fetchall()]

def save_new_posts(conn: sqlite3.Connection, posts: List[Dict]):
    with conn:
        conn.executemany(
            "INSERT OR IGNORE INTO posts (id, url, date_posted, media_type) VALUES (?, ?, ?, ?)",
            [(p["id"], p["url"], p["date_posted"], p["media_type"]) for p in posts],
        )
    logger.info("Saved {} new posts", len(posts))

# Ensure indexes exist for ingested_content when module imported
try:
    conn_idx = sqlite3.connect(Path(DOWNLOAD_DIR).parent / "content.db")
    conn_idx.execute("CREATE INDEX IF NOT EXISTS idx_ingest_date ON ingested_content(ingest_date);")
    conn_idx.execute("CREATE INDEX IF NOT EXISTS idx_source_type ON ingested_content(source_type);")
    conn_idx.close()
except Exception:
    pass

# ---------------------------------------------------------------------------
# Ingested content metadata helpers
# ---------------------------------------------------------------------------

def fetch_metadata(limit: int = 50, offset: int = 0, source_type: str | None = None):
    """Retrieve metadata rows for API.

    Results are ordered by ingest_date DESC.
    """
    import sqlite3

    db_path = DB_PATH.parent / ".." / "content.db"
    db_path = db_path.resolve()
    if not db_path.exists():
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        params = []
        query = "SELECT * FROM ingested_content"
        if source_type:
            query += " WHERE source_type = ?"
            params.append(source_type)
        query += " ORDER BY ingest_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cur = conn.execute(query, params)
        rows = [dict(r) for r in cur.fetchall()]
        return rows
    finally:
        conn.close()
