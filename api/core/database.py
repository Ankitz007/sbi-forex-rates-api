"""
Database utilities for the API.
"""

import logging
from contextlib import contextmanager
from typing import Any, Generator
from urllib import parse as urlparse

import pg8000.dbapi as pg8000

from api.core.config import settings
from api.models import FOREX_RATES_TABLE


class DatabaseManager:
    """Database connection manager."""

    def __init__(self):
        # Clean up DATABASE_URL from SQLAlchemy prefixes
        db_url = settings.DATABASE_URL
        if db_url.startswith(
            (
                "postgresql+psycopg://",
                "postgresql+psycopg2://",
                "cockroachdb+psycopg://",
            )
        ):
            db_url = db_url.replace("postgresql+psycopg://", "postgresql://")
            db_url = db_url.replace("postgresql+psycopg2://", "postgresql://")
            db_url = db_url.replace("cockroachdb+psycopg://", "postgresql://")
        self.connection_string = db_url

    @contextmanager
    def get_connection(self) -> Generator[Any, None, None]:
        """Get database connection context manager."""
        conn = None
        try:
            # Expect a URL like: postgresql://user:pass@host:port/dbname
            parsed = urlparse.urlparse(self.connection_string)

            user = parsed.username
            password = parsed.password
            host = parsed.hostname
            port = parsed.port
            database = parsed.path.lstrip("/") if parsed.path else None

            # Validate required URL components to satisfy type checkers and provide clearer errors
            if host is None:
                raise ValueError("DATABASE_URL is missing a hostname")
            if port is None:
                raise ValueError("DATABASE_URL is missing a port")
            if database is None:
                raise ValueError("DATABASE_URL is missing a database name")

            conn = pg8000.connect(
                user=user, password=password, host=host, port=port, database=database
            )
            yield conn
        finally:
            if conn:
                conn.close()

    @contextmanager
    def get_cursor(self) -> Generator[Any, None, None]:
        """Get database cursor context manager."""
        with self.get_connection() as conn:
            # pg8000 returns a standard DB-API connection with cursor()
            cur = conn.cursor()
            try:
                yield cur
            finally:
                try:
                    cur.close()
                except Exception:
                    pass

    def ensure_indexes(self) -> None:
        """Ensure database indexes exist (idempotent operation)."""
        logger = logging.getLogger(__name__)

        # Table name is internal constant; build simple SQL strings.
        index_queries = [
            f"CREATE UNIQUE INDEX IF NOT EXISTS uix_ticker_date_category ON {FOREX_RATES_TABLE} (ticker, date, category)",
            f"CREATE INDEX IF NOT EXISTS ix_forex_rates_date ON {FOREX_RATES_TABLE} (date)",
        ]

        try:
            with self.get_connection() as conn:
                cur = conn.cursor()
                try:
                    for query in index_queries:
                        try:
                            cur.execute(query)
                        except Exception as e:
                            logger.warning("Failed to create index: %s -- %s", query, e)
                finally:
                    try:
                        cur.close()
                    except Exception:
                        pass
                conn.commit()
        except Exception as e:
            logger.warning("ensure_indexes encountered an error: %s", e)


# Global database manager instance
db_manager = DatabaseManager()


def get_db():
    """Get database cursor - for compatibility with existing code."""
    return db_manager.get_cursor()
