import sqlite3
from pathlib import Path
from typing import Optional, Tuple

DB_PATH = Path("secrets/shorts_factory.sqlite")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS articles_seen (
        source TEXT NOT NULL,
        external_id TEXT NOT NULL,
        title TEXT,
        first_seen_ts DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (source, external_id)
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS videos_made (
        video_path TEXT PRIMARY KEY,
        title TEXT,
        uploaded_youtube INTEGER DEFAULT 0,
        uploaded_tiktok INTEGER DEFAULT 0,
        created_ts DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def already_seen(source: str, external_id: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM articles_seen WHERE source=? AND external_id=?", (source, external_id))
    row = c.fetchone()
    conn.close()
    return row is not None

def mark_seen(source: str, external_id: str, title: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO articles_seen (source, external_id, title) VALUES (?, ?, ?)", (source, external_id, title))
    conn.commit()
    conn.close()

def mark_video(video_path: str, title: str, yt: int, tt: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO videos_made (video_path, title, uploaded_youtube, uploaded_tiktok) VALUES (?, ?, ?, ?)",
              (video_path, title, yt, tt))
    conn.commit()
    conn.close()
