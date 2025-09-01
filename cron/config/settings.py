"""
Configuration and settings for the SBI FX Rates cron jobs.
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


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


@dataclass
class DatabaseConfig:
    """Database configuration."""

    url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://myuser:mypassword@localhost:5432/mydb"
    )
    table_name: str = "forex_rates"


@dataclass
class PDFConfig:
    """PDF processing configuration."""

    # Date formats
    pdf_date_format: str = "%d-%m-%Y"
    filename_date_format: str = "%Y-%m-%d"
    db_date_format: str = "%d-%m-%Y"

    # Processing settings
    max_pages: int = 2
    request_timeout: int = 30

    # URLs for fetching PDFs
    primary_url: str = (
        "https://www.sbi.co.in/documents/16012/1400784/FOREX_CARD_RATES.pdf"
    )
    fallback_url: str = "https://bank.sbi/documents/16012/1400784/FOREX_CARD_RATES.pdf"

    # Table headers
    table_headers: Optional[List[str]] = None

    def __post_init__(self):
        if self.table_headers is None:
            self.table_headers = [
                "CURRENCY",
                "TICKER",
                "TT BUY",
                "TT SELL",
                "BILL BUY",
                "BILL SELL",
                "FTC BUY",
                "FTC SELL",
                "CN BUY",
                "CN SELL",
            ]


@dataclass
class ProcessingConfig:
    """Processing configuration."""

    num_workers: int = 4
    pdf_files_dir: str = "pdf_files"


# Configuration instances
db_config = DatabaseConfig()
pdf_config = PDFConfig()
processing_config = ProcessingConfig()
