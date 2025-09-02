"""
Service layer for business logic.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Union

from api.core.database import db_manager
from api.models import FOREX_RATES_TABLE, ForexRate
from api.schemas import ForexRateResponse


class ForexRateService:
    """Service class for forex rate operations."""

    @staticmethod
    def get_rates_by_date(date: datetime) -> List[ForexRate]:
        """Get forex rates for a specific date."""
        target_date = date.date()

        query = f"""
            SELECT id, currency, ticker, tt_buy, tt_sell, bill_buy, bill_sell,
                   ftc_buy, ftc_sell, cn_buy, cn_sell, date, category
            FROM {FOREX_RATES_TABLE}
            WHERE date = %s
        """

        with db_manager.get_cursor() as cursor:
            cursor.execute(query, (target_date,))
            rows = cursor.fetchall()
            return [ForexRate.from_db_row(row) for row in rows]

    @staticmethod
    def convert_to_response(rate: ForexRate, original_date: str) -> ForexRateResponse:
        """Convert ForexRate model to response schema."""

        # Safe conversion to float, defaulting to 0.0 for None values
        def to_float(value: Optional[Union[float, Decimal]]) -> float:
            return float(value) if value is not None else 0.0

        return ForexRateResponse(
            id=rate.id,
            currency=rate.currency,
            ticker=rate.ticker,
            tt_buy=to_float(rate.tt_buy),
            tt_sell=to_float(rate.tt_sell),
            bill_buy=to_float(rate.bill_buy),
            bill_sell=to_float(rate.bill_sell),
            ftc_buy=to_float(rate.ftc_buy),
            ftc_sell=to_float(rate.ftc_sell),
            cn_buy=to_float(rate.cn_buy),
            cn_sell=to_float(rate.cn_sell),
            date=original_date,
            category=rate.category.value,
        )

    @staticmethod
    def check_dates_availability(start_dt: datetime, end_dt: datetime) -> List[str]:
        """
        Return which dates in the given range exist in the database.

        Returns dates formatted as DD-MM-YYYY strings.
        """
        start_date = start_dt.date()
        end_date = end_dt.date()

        # Safety check for large ranges
        span_days = (end_date - start_date).days
        if span_days < 0:
            return []
        if span_days > 730:  # 2 years max
            raise ValueError("Date range too large (max 730 days)")

        query = f"""
            SELECT DISTINCT date
            FROM {FOREX_RATES_TABLE}
            WHERE date BETWEEN %s AND %s
            ORDER BY date
        """

        with db_manager.get_cursor() as cursor:
            cursor.execute(query, (start_date, end_date))
            rows = cursor.fetchall()

            return [row[0].strftime("%d-%m-%Y") for row in rows if row[0] is not None]
