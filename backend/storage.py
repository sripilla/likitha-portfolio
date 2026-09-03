"""
Lightweight SQLite storage for contact-form submissions.

Why store them at all, when we also email them? Email can fail silently
(wrong SMTP creds, provider rate limit, spam-folder routing) — having a
durable local copy means no message is ever fully lost.
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .config import get_settings

settings = get_settings()


def _ensure_db_dir() -> None:
    Path(settings.DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection():
    _ensure_db_dir()
    conn = sqlite3.connect(settings.DATABASE_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL,
                submitted_at TEXT NOT NULL,
                email_sent INTEGER NOT NULL DEFAULT 0
            )
            """
        )


def save_submission(name: str, email: str, message: str, email_sent: bool) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO submissions (name, email, message, submitted_at, email_sent) "
            "VALUES (?, ?, ?, ?, ?)",
            (name, email, message, datetime.now(timezone.utc).isoformat(), int(email_sent)),
        )
