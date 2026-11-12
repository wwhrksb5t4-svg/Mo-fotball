import sqlite3
from pathlib import Path

import psycopg

from app.config import DATABASE_PATH, DATABASE_URL


class PostgresConnection:
    """Small adapter so existing parameterized queries work with SQLite or PostgreSQL."""

    def __init__(self, connection):
        self._connection = connection

    def execute(self, query: str, parameters=()):
        return self._connection.execute(query.replace("?", "%s"), parameters)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if exc_type is None:
                self._connection.commit()
            else:
                self._connection.rollback()
        finally:
            self._connection.close()
        return False


def _normalized_database_url() -> str:
    # Some platforms still provide the legacy postgres:// scheme.
    if DATABASE_URL.startswith("postgres://"):
        return "postgresql://" + DATABASE_URL[len("postgres://"):]
    return DATABASE_URL


def get_connection():
    if DATABASE_URL:
        return PostgresConnection(
            psycopg.connect(_normalized_database_url(), connect_timeout=15)
        )

    path = Path(DATABASE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    if DATABASE_URL:
        with get_connection() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS photo_records (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    file_path TEXT NOT NULL,
                    ocr_text TEXT,
                    created_at TIMESTAMPTZ NOT NULL
                )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS analysis_records (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    competition TEXT NOT NULL,
                    home_team TEXT NOT NULL,
                    away_team TEXT NOT NULL,
                    report TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL
                )"""
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_photos_user_created ON photo_records (user_id, created_at DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_analyses_user_created ON analysis_records (user_id, created_at DESC)")
        return

    with get_connection() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS photo_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                ocr_text TEXT,
                created_at TEXT NOT NULL
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS analysis_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                competition TEXT NOT NULL,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                report TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_photos_user_created ON photo_records (user_id, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_analyses_user_created ON analysis_records (user_id, created_at)")
