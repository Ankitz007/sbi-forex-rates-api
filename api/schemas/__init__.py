"""
Pydantic schemas for API request/response models.
"""

from typing import Any, List, Optional

from pydantic import BaseModel


class ForexRateResponse(BaseModel):
    """Response model for forex rate data."""

    id: int
    currency: str
    ticker: str
    tt_buy: float
    tt_sell: float
    bill_buy: float
    bill_sell: float
    ftc_buy: float
    ftc_sell: float
    cn_buy: float
    cn_sell: float
    date: str
    category: str


class StandardResponse(BaseModel):
    """Standard API response wrapper."""

    success: bool
    data: Any
    message: Optional[str] = None


class DateAvailabilityResponse(BaseModel):
    """Response model for date availability check."""

    success: bool
    data: List[str]  # List of available dates in DD-MM-YYYY format
    message: Optional[str] = None
