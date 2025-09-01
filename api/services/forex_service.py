"""
Service layer for business logic.
"""

from datetime import datetime
from typing import List

from sqlalchemy import text
from sqlalchemy.orm import Session

from api.models import ForexRate
from api.schemas import ForexRateResponse


class ForexRateService:
    """Service class for forex rate operations."""

    @staticmethod
    def get_rates_by_date(db: Session, date: datetime) -> List[ForexRate]:
        """
        Get forex rates for a specific date.

        Args:
            db: Database session
            date: Date to query

        Returns:
            List of ForexRate objects
        """
        return db.query(ForexRate).filter(ForexRate.date == date.date()).all()

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

    @staticmethod
    def check_dates_availability(
        db: Session, start_dt: datetime, end_dt: datetime
    ) -> List[str]:
        """
        Given an inclusive date range (start_dt, end_dt), return which dates in that range exist in the DB.

        Args:
            db: DB session
            start_dt: start datetime
            end_dt: end datetime

        Returns:
            List of date strings (DD-MM-YYYY) that exist in the DB within the range
        """
        # Ensure we compare dates (not datetimes)
        start_date = start_dt.date()
        end_date = end_dt.date()

        # Safety: don't allow ridiculously large ranges
        max_span_days = 365 * 2  # 2 years max
        if (end_date - start_date).days < 0:
            return []
        if (end_date - start_date).days > max_span_days:
            raise ValueError(f"Date range too large (max {max_span_days} days)")

        try:
            # Use BETWEEN to fetch distinct dates in the inclusive range
            stmt = text(
                "SELECT DISTINCT date FROM forex_rates WHERE date BETWEEN :start_date AND :end_date ORDER BY date"
            )

            result = db.execute(stmt, {"start_date": start_date, "end_date": end_date})

            found_dates = [row[0] for row in result.fetchall()]

            return [d.strftime("%d-%m-%Y") for d in found_dates]

        except Exception:
            raise
