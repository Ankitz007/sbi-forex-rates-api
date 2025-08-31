"""
Constants and configuration for the SBI FX Rates project.
"""

import os
from enum import Enum

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://myuser:mypassword@localhost:5432/mydb"
)

# Date formats used in this project
# PDF displays date as DD-MM-YYYY (e.g. 21-01-2022)
PDF_DATE_FORMAT = "%d-%m-%Y"
# Filenames are expected to be YYYY-MM-DD (e.g. 2022-01-21)
FILENAME_DATE_FORMAT = "%Y-%m-%d"

# Database storage format for dates (DD-MM-YYYY)
DB_DATE_FORMAT = "%d-%m-%Y"


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


# Table name
FOREX_RATES_TABLE = "forex_rates"
