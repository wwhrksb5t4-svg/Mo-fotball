import sqlite3
from pathlib import Path

import psycopg

from app.config import DATABASE_PATH, DATABASE_URL


class Connection:
    """Uniform context manager for SQLite and PostgreSQL connections."""

    def __init__(self, connection, postgres: bool):
        self.connection = connection
        self.postgres = postgres

    def execute(self, query: str, parameters=()):
        if self.postgres:
            query = query.replace("?", "%s")
        return self.connection.execute(query, parameters)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if exc_type is None:
                self.connection.commit()
            else:
                self.connection.rollback()
        finally:
            self.connection.close()
        return False


def _postgres_url() -> str:
    if DATABASE_URL.startswith("postgres://"):
        return "postgresql://" + DATABASE_URL[len("postgres://"):]
    return DATABASE_URL


def get_connection() -> Connection:
    if DATABASE_URL:
        return Connection(psycopg.connect(_postgres_url(), connect_timeout=15), postgres=True)

    db_path = Path(DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, timeout=30)
    connection.row_factory = sqlite3.Row
    return Connection(connection, postgres=False)


def init_db() -> None:
    if DATABASE_URL:
        photo_id = "BIGSERIAL PRIMARY KEY"
        created_at = "TIMESTAMPTZ NOT NULL"
    else:
        photo_id = "INTEGER PRIMARY KEY AUTOINCREMENT"
        created_at = "TEXT NOT NULL"

    with get_connection() as conn:
        conn.execute(
            f"""CREATE TABLE IF NOT EXISTS photo_records (
                id {photo_id}, user_id BIGINT NOT NULL, file_path TEXT NOT NULL,
                ocr_text TEXT, created_at {created_at}
            )"""
        )
        conn.execute(
            f"""CREATE TABLE IF NOT EXISTS analysis_records (
                id {photo_id}, user_id BIGINT NOT NULL, competition TEXT NOT NULL,
                home_team TEXT NOT NULL, away_team TEXT NOT NULL,
                report TEXT NOT NULL, created_at {created_at}
            )"""
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_photos_user_created ON photo_records (user_id, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_analyses_user_created ON analysis_records (user_id, created_at)")
