"""
Database utilities for the SBI FX Rates project.
"""

import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional

from constants import DATABASE_URL, TransactionCategory
from models import Base, ForexRate
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self, database_url: str = DATABASE_URL):
        """Initialize database manager with connection URL."""
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None

    def connect(self) -> bool:
        """Connect to the database and create tables if needed."""
        try:
            self.engine = create_engine(self.database_url)
            self.SessionLocal = sessionmaker(bind=self.engine)

            # Create tables if they don't exist using per-table create with
            # checkfirst=True which issues CREATE TABLE IF NOT EXISTS when
            # supported by the dialect.
            for table in Base.metadata.sorted_tables:
                try:
                    table.create(self.engine, checkfirst=True)
                except SQLAlchemyError as e:
                    logger.error(f"Failed to create table {table.name}: {e}")
                    return False
            return True

        except SQLAlchemyError as e:
            logger.error(f"Failed to connect to database: {e}")
            return False

    def get_session(self) -> Session:
        """Get a new database session."""
        if not self.SessionLocal:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.SessionLocal()

    def insert_forex_records(self, records: List[Dict]) -> bool:
        """Insert or update forex rate records in the database."""
        if not records:
            logger.warning("No records to insert")
            return True

        # Convert incoming records to DB-ready dicts and filter out invalid ones
        values = []
        for record in records:
            forex_rate_data = self._record_to_dict(record)
            if not forex_rate_data:
                continue
            values.append(forex_rate_data)

        if not values:
            logger.warning("No valid records after conversion")
            return True

        session = self.get_session()
        try:
            # Build a Postgres INSERT ... ON CONFLICT DO UPDATE statement
            insert_stmt = pg_insert(ForexRate.__table__).values(values)

            # Columns to update on conflict: update all updatable columns except id and
            # the conflict target columns (ticker, date, category).
            excluded = insert_stmt.excluded
            update_cols = {
                "currency": excluded.currency,
                "tt_buy": excluded.tt_buy,
                "tt_sell": excluded.tt_sell,
                "bill_buy": excluded.bill_buy,
                "bill_sell": excluded.bill_sell,
                "ftc_buy": excluded.ftc_buy,
                "ftc_sell": excluded.ftc_sell,
                "cn_buy": excluded.cn_buy,
                "cn_sell": excluded.cn_sell,
            }

            stmt = insert_stmt.on_conflict_do_update(
                index_elements=["ticker", "date", "category"],
                set_=update_cols,
            )

            session.execute(stmt)
            session.commit()
            logger.info("Upserted %d forex records", len(values))
            return True

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to upsert records: {e}")
            return False
        finally:
            session.close()

    def _record_to_dict(self, record: Dict) -> Optional[Dict]:
        """Convert a record dict to a dict suitable for ForexRate model."""
        try:
            # Convert category text to enum
            category = TransactionCategory.from_pdf_text(record.get("category", ""))

            # Convert date from ISO format (YYYY-MM-DD) to a Python date
            iso_date = record.get("date", "")
            if iso_date:
                dt = datetime.strptime(iso_date, "%Y-%m-%d").date()
                db_date = dt
            else:
                db_date = None

            return {
                "currency": record.get("name", ""),
                "ticker": record.get("ticker", ""),
                "tt_buy": self._safe_decimal(record.get("tt_buy")),
                "tt_sell": self._safe_decimal(record.get("tt_sell")),
                "bill_buy": self._safe_decimal(record.get("bill_buy")),
                "bill_sell": self._safe_decimal(record.get("bill_sell")),
                "ftc_buy": self._safe_decimal(record.get("ftc_buy")),
                "ftc_sell": self._safe_decimal(record.get("ftc_sell")),
                "cn_buy": self._safe_decimal(record.get("cn_buy")),
                "cn_sell": self._safe_decimal(record.get("cn_sell")),
                "date": db_date,
                "category": category,
            }

        except Exception as e:
            logger.error(f"Failed to convert record to dict: {record}, error: {e}")
            return None

    def _safe_decimal(self, value) -> Decimal:
        """Safely convert string to Decimal, returning 0 for invalid values."""
        if not value or value == "0":
            return Decimal("0")
        try:
            return Decimal(str(value).strip())
        except (InvalidOperation, ValueError):
            logger.debug(f"Invalid decimal value: {value}, defaulting to 0")
            return Decimal("0")

    def test_connection(self) -> bool:
        """Test the database connection."""
        try:
            from sqlalchemy import text

            session = self.get_session()
            # Simple query to test connection
            session.execute(text("SELECT 1"))
            session.close()
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()
