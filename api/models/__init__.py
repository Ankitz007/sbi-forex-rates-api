"""
Database models for the SBI FX Rates API.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

# Constants
FOREX_RATES_TABLE = "forex_rates"


class TransactionCategory(Enum):
    """Enum for transaction categories."""

    BELOW_10 = "below_10"
    TEN_TO_TWENTY = "10_to_20"

    @classmethod
    def from_pdf_text(cls, text: str) -> "TransactionCategory":
        """Map PDF text to enum values."""
        return cls.TEN_TO_TWENTY if "BETWEEN" in text.upper() else cls.BELOW_10

    @classmethod
    def from_db_value(cls, val) -> "TransactionCategory":
        """Create enum from database value with flexible parsing."""
        if not val:
            return cls.BELOW_10

        if isinstance(val, cls):
            return val

        if isinstance(val, str):
            # Try direct value lookup first
            for member in cls:
                if member.value == val or member.name == val.upper():
                    return member

            # Case-insensitive fallback
            for member in cls:
                if member.value.lower() == val.lower():
                    return member

        raise ValueError(f"'{val}' is not a valid {cls.__name__}")


@dataclass
class ForexRate:
    """Data model for forex rates."""

    id: int
    currency: str
    ticker: str
    tt_buy: Decimal
    tt_sell: Decimal
    bill_buy: Decimal
    bill_sell: Decimal
    ftc_buy: Decimal
    ftc_sell: Decimal
    cn_buy: Decimal
    cn_sell: Decimal
    date: date
    category: TransactionCategory

    @classmethod
    def from_db_row(cls, row) -> "ForexRate":
        """Create ForexRate instance from database row."""
        return cls(
            id=row[0],
            currency=row[1],
            ticker=row[2],
            tt_buy=row[3],
            tt_sell=row[4],
            bill_buy=row[5],
            bill_sell=row[6],
            ftc_buy=row[7],
            ftc_sell=row[8],
            cn_buy=row[9],
            cn_sell=row[10],
            date=row[11],
            category=TransactionCategory.from_db_value(row[12]),
        )

    def __repr__(self) -> str:
        return f"ForexRate(ticker={self.ticker!r}, date={self.date!r}, category={self.category.value!r})"
