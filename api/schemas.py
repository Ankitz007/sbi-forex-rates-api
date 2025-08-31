"""
Pydantic schemas for API request/response models.
"""

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


class ErrorResponse(BaseModel):
    """Response model for errors."""

    detail: str
