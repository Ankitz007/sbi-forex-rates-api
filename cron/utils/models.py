"""
Models for the forex rates database.
"""

from config.settings import TransactionCategory, db_config
from sqlalchemy import Column, Date
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ForexRate(Base):
    """SQLAlchemy model for forex rates table."""

    __tablename__ = db_config.table_name
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
