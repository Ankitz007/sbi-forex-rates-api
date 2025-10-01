"""
Database service for handling forex rate data operations.
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional

from config.settings import TransactionCategory, db_config
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from utils.logger import LoggerFactory
from utils.models import Base, ForexRate

logger = LoggerFactory.get_logger(__name__)


class DatabaseService:
    """Service for managing database connections and forex rate operations."""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database service with connection URL.

        Args:
            database_url: Database connection URL. Uses config default if None.
        """
        self.database_url = database_url or db_config.url
        self.engine = None
        self.SessionLocal = None
        self._connected = False

    def connect(self) -> bool:
        """
        Connect to the database and create tables if needed.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.engine = create_engine(self.database_url)
            self.SessionLocal = sessionmaker(bind=self.engine)

            # Create tables if they don't exist
            for table in Base.metadata.sorted_tables:
                try:
                    table.create(self.engine, checkfirst=True)
                except SQLAlchemyError as e:
                    logger.error("Failed to create table %s: %s", table.name, e)
                    return False

            self._connected = True
            logger.debug("Successfully connected to database")
            return True

        except SQLAlchemyError as e:
            logger.error("Failed to connect to database: %s", e)
            return False

    def get_session(self) -> Session:
        """
        Get a new database session.

        Returns:
            Database session

        Raises:
            RuntimeError: If database not connected
        """
        if not self._connected or not self.SessionLocal:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.SessionLocal()

    def insert_forex_records(self, records: List[Dict]) -> bool:
        """
        Insert or update forex rate records in the database.

        Args:
            records: List of forex rate records as dictionaries

        Returns:
            True if successful, False otherwise
        """
        if not records:
            logger.warning("No records to insert")
            return True

        # Convert and validate records
        values = []
        for record in records:
            forex_rate_data = self._record_to_dict(record)
            if forex_rate_data:
                values.append(forex_rate_data)

        if not values:
            logger.warning("No valid records after conversion")
            return True

        session = self.get_session()
        try:
            # Build PostgreSQL INSERT ... ON CONFLICT DO UPDATE statement
            insert_stmt = pg_insert(ForexRate.__table__).values(values)

            # Define columns to update on conflict
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
            logger.debug("Successfully upserted %d forex records", len(values))
            return True

        except SQLAlchemyError as e:
            session.rollback()
            logger.error("Failed to upsert records: %s", e)
            return False
        finally:
            session.close()

    def test_connection(self) -> bool:
        """
        Test the database connection.

        Returns:
            True if connection test successful, False otherwise
        """
        try:
            from sqlalchemy import text

            session = self.get_session()
            session.execute(text("SELECT 1"))
            session.close()
            logger.debug("Database connection test successful")
            return True
        except Exception as e:
            logger.error("Database connection test failed: %s", e)
            return False

    def _record_to_dict(self, record: Dict) -> Optional[Dict]:
        """
        Convert a record dict to a dict suitable for ForexRate model.

        Args:
            record: Input record dictionary

        Returns:
            Converted record dictionary or None if conversion failed
        """
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
            logger.error("Failed to convert record to dict: %s, error: %s", record, e)
            return None

    def _safe_decimal(self, value) -> Decimal:
        """
        Safely convert string to Decimal, returning 0 for invalid values.

        Args:
            value: Value to convert

        Returns:
            Decimal value or 0 if conversion fails
        """
        if not value or value == "0":
            return Decimal("0")
        try:
            return Decimal(str(value).strip())
        except (InvalidOperation, ValueError):
            logger.debug("Invalid decimal value: %s, defaulting to 0", value)
            return Decimal("0")
