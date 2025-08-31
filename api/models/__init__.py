"""
Database models for the SBI FX Rates API.
"""

from enum import Enum

from sqlalchemy import Column, Date
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Constants
FOREX_RATES_TABLE = "forex_rates"


class TransactionCategory(Enum):
    """Enum for transaction categories."""

    BELOW_10 = "below_10"
    TEN_TO_TWENTY = "10_to_20"

    @classmethod
    def from_pdf_text(cls, text: str) -> "TransactionCategory":
        """Map PDF text to enum values."""
        text_upper = text.upper()
        if "BELOW" in text_upper:
            return cls.BELOW_10
        elif "BETWEEN" in text_upper:
            return cls.TEN_TO_TWENTY
        else:
            # Default fallback
            return cls.BELOW_10


class ForexRate(Base):
    """SQLAlchemy model for forex rates table."""

    __tablename__ = FOREX_RATES_TABLE
    # Unique constraint plus an index on date for faster lookups by date
    __table_args__ = (
        UniqueConstraint("ticker", "date", "category", name="uix_ticker_date_category"),
        Index("ix_forex_rates_date", "date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    currency = Column(String, nullable=False)  # e.g., "United States Dollar"
    ticker = Column(String, nullable=False)  # e.g., "USD"
    tt_buy = Column(Numeric(10, 2), nullable=False, default=0)
    tt_sell = Column(Numeric(10, 2), nullable=False, default=0)
    bill_buy = Column(Numeric(10, 2), nullable=False, default=0)
    bill_sell = Column(Numeric(10, 2), nullable=False, default=0)
    ftc_buy = Column(Numeric(10, 2), nullable=False, default=0)
    ftc_sell = Column(Numeric(10, 2), nullable=False, default=0)
    cn_buy = Column(Numeric(10, 2), nullable=False, default=0)
    cn_sell = Column(Numeric(10, 2), nullable=False, default=0)
    date = Column(Date, nullable=False)  # Stored as a SQL Date
    category = Column(SQLEnum(TransactionCategory), nullable=False)

    def __repr__(self):
        return f"<ForexRate(ticker='{self.ticker}', date='{self.date}', category='{self.category}')>"
