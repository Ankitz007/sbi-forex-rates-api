"""
Response schemas for API endpoints.
"""

from dataclasses import asdict, dataclass
from typing import Any, List, Optional


@dataclass
class ForexRateResponse:
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

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class StandardResponse:
    """Standard API response wrapper."""

    success: bool
    data: Any
    message: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        # Handle nested objects that might have to_dict methods
        if isinstance(self.data, list):
            result["data"] = [
                item.to_dict() if hasattr(item, "to_dict") else item
                for item in self.data
            ]
        elif hasattr(self.data, "to_dict"):
            result["data"] = self.data.to_dict()
        return result


@dataclass
class DateAvailabilityResponse:
    """Response model for date availability check."""

    success: bool
    data: List[str]
    message: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
