"""
Database utilities for the API.
"""

import logging
from contextlib import contextmanager
from typing import Generator

import psycopg
from psycopg import sql

from api.core.config import settings
from api.models import FOREX_RATES_TABLE


class DatabaseManager:
    """Database connection manager."""

    def __init__(self):
        # Clean up DATABASE_URL from SQLAlchemy prefixes
        db_url = settings.DATABASE_URL
        if db_url.startswith(("postgresql+psycopg://", "postgresql+psycopg2://")):
            db_url = db_url.replace("postgresql+psycopg://", "postgresql://")
            db_url = db_url.replace("postgresql+psycopg2://", "postgresql://")
        self.connection_string = db_url

    @contextmanager
    def get_connection(self) -> Generator[psycopg.Connection, None, None]:
        """Get database connection context manager."""
        conn = None
        try:
            conn = psycopg.connect(self.connection_string)
            yield conn
        finally:
            if conn:
                conn.close()

    @contextmanager
    def get_cursor(self) -> Generator[psycopg.Cursor, None, None]:
        """Get database cursor context manager."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                yield cursor

    def ensure_indexes(self) -> None:
        """Ensure database indexes exist (idempotent operation)."""
        logger = logging.getLogger(__name__)

        index_queries = [
            sql.SQL(
                "CREATE UNIQUE INDEX IF NOT EXISTS uix_ticker_date_category ON {} (ticker, date, category)"
            ).format(sql.Identifier(FOREX_RATES_TABLE)),
            sql.SQL(
                "CREATE INDEX IF NOT EXISTS ix_forex_rates_date ON {} (date)"
            ).format(sql.Identifier(FOREX_RATES_TABLE)),
        ]

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    for query in index_queries:
                        try:
                            cur.execute(query)
                        except Exception as e:
                            logger.warning("Failed to create index: %s -- %s", query, e)
                conn.commit()
        except Exception as e:
            logger.warning("ensure_indexes encountered an error: %s", e)


# Global database manager instance
db_manager = DatabaseManager()


def get_db():
    """Get database cursor - for compatibility with existing code."""
    return db_manager.get_cursor()
