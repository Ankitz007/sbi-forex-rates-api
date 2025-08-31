"""
Service layer for business logic.
"""

from datetime import datetime
from typing import List, Optional

from models import ForexRate
from schemas import ForexRateResponse
from sqlalchemy.orm import Session


class ForexRateService:
    """Service class for forex rate operations."""

    @staticmethod
    def get_rates_by_date(
        db: Session, date: datetime, ticker: Optional[str] = None
    ) -> List[ForexRate]:
        """
        Get forex rates for a specific date.

        Args:
            db: Database session
            date: Date to query
            ticker: Optional ticker filter

        Returns:
            List of ForexRate objects
        """
        query = db.query(ForexRate).filter(ForexRate.date == date.date())

        if ticker:
            query = query.filter(ForexRate.ticker == ticker.upper())

        return query.all()

    @staticmethod
    def convert_to_response(rate, original_date: str) -> ForexRateResponse:
        """
        Convert ForexRate model to response schema.

        Args:
            rate: ForexRate model instance
            original_date: Original date string for response

        Returns:
            ForexRateResponse instance
        """
        return ForexRateResponse(
            id=rate.id,
            currency=rate.currency,
            ticker=rate.ticker,
            tt_buy=float(rate.tt_buy),
            tt_sell=float(rate.tt_sell),
            bill_buy=float(rate.bill_buy),
            bill_sell=float(rate.bill_sell),
            ftc_buy=float(rate.ftc_buy),
            ftc_sell=float(rate.ftc_sell),
            cn_buy=float(rate.cn_buy),
            cn_sell=float(rate.cn_sell),
            date=original_date,
            category=rate.category.value,
        )
